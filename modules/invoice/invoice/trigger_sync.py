"""
Service for keeping DB code-generation triggers in sync with model schema and config.

Compares structured components (column sets, code pattern) rather than raw SQL text
to avoid false positives from formatting differences.
"""
import logging
import re

from django.db import connection

logger = logging.getLogger(__name__)

# Pattern tokens → SQL fragments per vendor
_TOKEN_SQL = {
    'postgresql': {
        '[YY]': "to_char(now(), 'YY')",
        '[YYYY]': "to_char(now(), 'YYYY')",
        '[MM]': "to_char(now(), 'MM')",
    },
    'microsoft': {
        '[YY]': "RIGHT(CONVERT(VARCHAR(4), YEAR(GETDATE())), 2)",
        '[YYYY]': "CONVERT(VARCHAR(4), YEAR(GETDATE()))",
        '[MM]': "RIGHT('00' + CONVERT(VARCHAR(2), MONTH(GETDATE())), 2)",
    },
}

DEFAULT_BILL_CODE_PATTERN = "BIL-[YY]-[SEQ:10]"
DEFAULT_BENEFIT_CODE_PATTERN = "BEN-[YY]-[SEQ:10]"

# Characters allowed in pattern literals (letters, digits, common separators)
_SAFE_LITERAL_RE = re.compile(r'^[A-Za-z0-9\-_/. ]+$')
# SQL identifiers: alphanumerics + underscore only
_SAFE_IDENTIFIER_RE = re.compile(r'^[A-Za-z_]\w*$')


def validate_pattern(pattern):
    """Validate a code pattern. Raises ValueError if invalid."""
    segments = parse_pattern(pattern)
    seq_count = sum(1 for t, v in segments if v.startswith('[SEQ'))
    if seq_count != 1:
        raise ValueError(f"Pattern must contain exactly one [SEQ] or [SEQ:N] token, found {seq_count}: {pattern}")
    for seg_type, value in segments:
        if seg_type == 'literal' and not _SAFE_LITERAL_RE.match(value):
            raise ValueError(f"Pattern literal contains unsafe characters: {value!r}")
    return True


def parse_pattern(pattern):
    """Parse a code pattern into a list of (type, value) segments.

    E.g. "BIL-[YY]-[SEQ:10]" → [('literal','BIL-'), ('token','[YY]'), ('literal','-'), ('token','[SEQ:10]')]
    """
    segments = []
    pos = 0
    for match in re.finditer(r'\[(?:SEQ(?::\d+)?|YY|YYYY|MM)\]', pattern):
        if match.start() > pos:
            segments.append(('literal', pattern[pos:match.start()]))
        segments.append(('token', match.group()))
        pos = match.end()
    if pos < len(pattern):
        segments.append(('literal', pattern[pos:]))
    return segments


def _seq_token_pad(token):
    """Extract pad width from [SEQ:N], default 10. Range: 1-20."""
    m = re.match(r'\[SEQ(?::(\d+))?\]', token)
    pad = int(m.group(1)) if m and m.group(1) else 10
    if pad < 1 or pad > 20:
        raise ValueError(f"Sequence padding width must be between 1 and 20, got {pad}")
    return pad


def pattern_to_pg_expr(pattern, sequence_name):
    """Convert pattern to PostgreSQL expression for use in trigger."""
    segments = parse_pattern(pattern)
    parts = []
    for seg_type, value in segments:
        if seg_type == 'literal':
            parts.append(f"'{value}'")
        elif value.startswith('[SEQ'):
            if ':' in value:
                pad = _seq_token_pad(value)
                parts.append(f"lpad(nextval('{sequence_name}')::text, {pad}, '0')")
            else:
                parts.append(f"nextval('{sequence_name}')::text")
        else:
            parts.append(_TOKEN_SQL['postgresql'][value])
    return ' || '.join(parts)


def pattern_to_mssql_expr(pattern, sequence_name):
    """Convert pattern to MSSQL expression for use in trigger."""
    segments = parse_pattern(pattern)
    parts = []
    for seg_type, value in segments:
        if seg_type == 'literal':
            parts.append(f"'{value}'")
        elif value.startswith('[SEQ'):
            if ':' in value:
                pad = _seq_token_pad(value)
                zeros = '0' * pad
                parts.append(
                    f"RIGHT('{zeros}' + CAST(NEXT VALUE FOR {sequence_name} AS VARCHAR(20)), {pad})"
                )
            else:
                parts.append(f"CAST(NEXT VALUE FOR {sequence_name} AS VARCHAR(20))")
        else:
            parts.append(_TOKEN_SQL['microsoft'][value])
    return ' + '.join(parts)


def _get_model_columns(model):
    """Get the set of actual DB column names for a model."""
    return {f.column for f in model._meta.concrete_fields}


def _get_pg_function_body(trigger_function_name):
    """Retrieve the PG function body from pg_proc."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT prosrc FROM pg_proc WHERE proname = %s",
            [trigger_function_name],
        )
        row = cursor.fetchone()
    return row[0] if row else None


def _get_pg_trigger_code_expr(trigger_function_name):
    """Extract the code-generation expression from PG trigger body."""
    body = _get_pg_function_body(trigger_function_name)
    if not body:
        return None
    # The expression is between the assignment := and the semicolon after it
    m = re.search(r':=\s*(.+?);', body, re.DOTALL)
    return m.group(1).strip() if m else None


def _get_mssql_trigger_columns(trigger_name):
    """Extract the INSERT column list from an MSSQL trigger definition."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT OBJECT_DEFINITION(OBJECT_ID(%s))",
            [trigger_name],
        )
        row = cursor.fetchone()
    if not row or not row[0]:
        return None, None

    body = row[0]

    # Extract INSERT INTO [table] (...) column list
    insert_match = re.search(
        r'INSERT\s+INTO\s+\[?\w+\]?\s*\(([^)]+)\)',
        body, re.IGNORECASE | re.DOTALL,
    )
    if insert_match:
        raw_cols = insert_match.group(1)
        columns = {
            m.group(1)
            for m in re.finditer(r'\[(\w+)\]', raw_cols)
        }
    else:
        columns = None

    # Extract the CASE expression for code generation
    case_match = re.search(r'(CASE\s+WHEN.*?END)', body, re.IGNORECASE | re.DOTALL)
    code_expr = case_match.group(1).strip() if case_match else None

    return columns, code_expr


def build_pg_trigger_sql(model, sequence_name, trigger_name, function_name, code_column, pattern):
    """Generate complete PG trigger SQL."""
    table = model._meta.db_table
    code_expr = pattern_to_pg_expr(pattern, sequence_name)

    return f"""
        CREATE OR REPLACE FUNCTION {function_name}()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW."{code_column}" IS NULL OR NEW."{code_column}" = '' THEN
                NEW."{code_column}" := {code_expr};
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS {trigger_name} ON "{table}";
        CREATE TRIGGER {trigger_name}
            BEFORE INSERT ON "{table}"
            FOR EACH ROW EXECUTE FUNCTION {function_name}();
    """


def build_mssql_trigger_sql(model, sequence_name, trigger_name, code_column, pattern):
    """Generate complete MSSQL INSTEAD OF INSERT trigger SQL."""
    table = model._meta.db_table
    columns = [f.column for f in model._meta.concrete_fields]
    code_expr = pattern_to_mssql_expr(pattern, sequence_name)

    col_list = ', '.join(f'[{c}]' for c in columns)
    select_parts = []
    for c in columns:
        if c == code_column:
            select_parts.append(
                f"CASE\n"
                f"                    WHEN i.[{c}] IS NULL OR i.[{c}] = ''\n"
                f"                        THEN {code_expr}\n"
                f"                    ELSE i.[{c}]\n"
                f"                END"
            )
        else:
            select_parts.append(f'i.[{c}]')
    select_list = ',\n                '.join(select_parts)

    return f"""
        CREATE TRIGGER [{trigger_name}]
        ON [{table}]
        INSTEAD OF INSERT
        AS
        BEGIN
            SET NOCOUNT ON;
            INSERT INTO [{table}] (
                {col_list}
            )
            SELECT
                {select_list}
            FROM inserted i;
        END
    """


def sync_trigger(
    model,
    sequence_name,
    trigger_name,
    code_column,
    pattern,
    pg_function_name=None,
    dry_run=False,
):
    """Check if the DB trigger matches current model schema + pattern. Recreate if not.

    Returns True if trigger was updated, False if already in sync, None if unsupported vendor.
    """
    validate_pattern(pattern)
    for name, value in [('trigger_name', trigger_name), ('sequence_name', sequence_name), ('code_column', code_column)]:
        if not _SAFE_IDENTIFIER_RE.match(value):
            raise ValueError(f"Unsafe SQL identifier for {name}: {value!r}")
    if pg_function_name and not _SAFE_IDENTIFIER_RE.match(pg_function_name):
        raise ValueError(f"Unsafe SQL identifier for pg_function_name: {pg_function_name!r}")
    vendor = connection.vendor

    if vendor == 'postgresql':
        fn_name = pg_function_name or f'set_{model._meta.db_table.lower()}_code'
        return _sync_pg_trigger(model, sequence_name, trigger_name, fn_name, code_column, pattern, dry_run)
    elif vendor == 'microsoft':
        return _sync_mssql_trigger(model, sequence_name, trigger_name, code_column, pattern, dry_run)
    else:
        logger.debug(f"Trigger sync skipped: unsupported vendor '{vendor}'")
        return None


def _sync_pg_trigger(model, sequence_name, trigger_name, function_name, code_column, pattern, dry_run):
    """Sync PG trigger. Compare code expression pattern."""
    current_expr = _get_pg_trigger_code_expr(function_name)
    expected_expr = pattern_to_pg_expr(pattern, sequence_name)

    if current_expr and _normalize_sql(current_expr) == _normalize_sql(expected_expr):
        logger.debug(f"PG trigger '{trigger_name}' is in sync")
        return False

    if dry_run:
        logger.info(f"[DRY RUN] PG trigger '{trigger_name}' needs update")
        if current_expr:
            logger.info(f"  Current expr: {current_expr}")
        logger.info(f"  Expected expr: {expected_expr}")
        return True

    logger.info(f"Recreating PG trigger '{trigger_name}' (pattern or function changed)")
    sql = build_pg_trigger_sql(model, sequence_name, trigger_name, function_name, code_column, pattern)
    with connection.cursor() as cursor:
        cursor.execute(sql)
    return True


def _sync_mssql_trigger(model, sequence_name, trigger_name, code_column, pattern, dry_run):
    """Sync MSSQL trigger. Compare column set + code expression."""
    db_columns, db_code_expr = _get_mssql_trigger_columns(trigger_name)
    expected_columns = _get_model_columns(model)

    columns_match = db_columns is not None and db_columns == expected_columns

    expected_code_expr = pattern_to_mssql_expr(pattern, sequence_name)
    code_match = (
        db_code_expr is not None
        and _normalize_sql(expected_code_expr) in _normalize_sql(db_code_expr)
    )

    if columns_match and code_match:
        logger.debug(f"MSSQL trigger '{trigger_name}' is in sync")
        return False

    reasons = []
    if not columns_match:
        if db_columns is not None:
            missing = expected_columns - db_columns
            extra = db_columns - expected_columns
            if missing:
                reasons.append(f"missing columns: {missing}")
            if extra:
                reasons.append(f"extra columns: {extra}")
        else:
            reasons.append("trigger not found")
    if not code_match:
        reasons.append("code pattern changed")

    if dry_run:
        logger.info(f"[DRY RUN] MSSQL trigger '{trigger_name}' needs update: {', '.join(reasons)}")
        return True

    logger.info(f"Recreating MSSQL trigger '{trigger_name}': {', '.join(reasons)}")

    # DROP first — CREATE TRIGGER must be first statement in batch on MSSQL
    with connection.cursor() as cursor:
        cursor.execute(f"""
            IF OBJECT_ID('{trigger_name}', 'TR') IS NOT NULL
                DROP TRIGGER [{trigger_name}];
        """)
    with connection.cursor() as cursor:
        sql = build_mssql_trigger_sql(model, sequence_name, trigger_name, code_column, pattern)
        cursor.execute(sql)
    return True


def _normalize_sql(sql):
    """Collapse whitespace for SQL comparison."""
    return re.sub(r'\s+', ' ', sql.strip().lower())


def refresh_trigger_codes(created, model, batch_size=500):
    """Re-fetch DB-trigger-assigned codes and patch history records.

    Call after bulk_create_with_history for models with DB trigger code generation.
    Returns the same `created` list with codes populated in-place.
    """
    empty_code_items = [b for b in created if not b.code]
    if not empty_code_items:
        return created

    history_model = model.history.model
    for i in range(0, len(empty_code_items), batch_size):
        chunk = empty_code_items[i:i + batch_size]
        chunk_ids = [b.id for b in chunk]
        refreshed = {
            b.id: b.code
            for b in model.objects.filter(id__in=chunk_ids).only('id', 'code')
        }
        for b in chunk:
            if b.id in refreshed:
                b.code = refreshed[b.id]
        history_records = list(history_model.objects.filter(
            id__in=chunk_ids, history_type='+', code='',
        ))
        for h in history_records:
            code = refreshed.get(h.id)
            if code:
                h.code = code
        updated_history = [h for h in history_records if h.code]
        if updated_history:
            history_model.objects.bulk_update(updated_history, ['code'])

    return created
