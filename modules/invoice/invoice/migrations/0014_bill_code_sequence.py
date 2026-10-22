from django.db import migrations


# ── PostgreSQL ────────────────────────────────────────────────────────────────

def _pg_apply(schema_editor):
    schema_editor.execute("CREATE SEQUENCE IF NOT EXISTS bill_code_seq;")
    schema_editor.execute("""
        DO $$
        DECLARE max_val BIGINT;
        BEGIN
            SELECT COALESCE(MAX(
                CASE WHEN "Code" ~ '^[0-9]+$' THEN "Code"::BIGINT
                     WHEN "Code" ~ '-([0-9]+)$' THEN (regexp_match("Code", '-([0-9]+)$'))[1]::BIGINT
                     ELSE 0 END
            ), 0) INTO max_val FROM "tblBill";
            IF max_val > 0 THEN PERFORM setval('bill_code_seq', max_val); END IF;
        END $$;
    """)
    schema_editor.execute("""
        CREATE OR REPLACE FUNCTION set_bill_code()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW."Code" IS NULL OR NEW."Code" = '' THEN
                NEW."Code" := 'BIL-' || to_char(now(), 'YY') || '-'
                              || lpad(nextval('bill_code_seq')::text, 10, '0');
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS bill_code_trigger ON "tblBill";
        CREATE TRIGGER bill_code_trigger
            BEFORE INSERT ON "tblBill"
            FOR EACH ROW EXECUTE FUNCTION set_bill_code();
    """)


def _pg_reverse(schema_editor):
    schema_editor.execute('DROP TRIGGER IF EXISTS bill_code_trigger ON "tblBill";')
    schema_editor.execute("DROP FUNCTION IF EXISTS set_bill_code();")
    schema_editor.execute("DROP SEQUENCE IF EXISTS bill_code_seq;")


# ── MSSQL (SQL Server 2012+) ──────────────────────────────────────────────────

def _mssql_apply(schema_editor):
    schema_editor.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.sequences WHERE object_id = OBJECT_ID('bill_code_seq'))
            EXEC('CREATE SEQUENCE bill_code_seq AS BIGINT START WITH 1 INCREMENT BY 1');
    """)
    schema_editor.execute("""
        DECLARE @max_val BIGINT = 0;
        SELECT @max_val = COALESCE(MAX(
            CASE
                WHEN [Code] LIKE '%-%'
                    THEN TRY_CAST(
                        REVERSE(LEFT(REVERSE([Code]), CHARINDEX('-', REVERSE([Code])) - 1))
                        AS BIGINT)
                WHEN [Code] NOT LIKE '%[^0-9]%' AND LEN([Code]) > 0
                    THEN TRY_CAST([Code] AS BIGINT)
                ELSE 0
            END
        ), 0) FROM [tblBill];
        IF @max_val > 0
            EXEC(N'ALTER SEQUENCE bill_code_seq RESTART WITH ' + CAST(@max_val + 1 AS NVARCHAR(20)));
    """)
    schema_editor.execute("""
        IF OBJECT_ID('bill_code_trigger', 'TR') IS NOT NULL
            DROP TRIGGER [bill_code_trigger];
    """)
    schema_editor.execute("""
        CREATE TRIGGER [bill_code_trigger]
        ON [tblBill]
        INSTEAD OF INSERT
        AS
        BEGIN
            SET NOCOUNT ON;
            INSERT INTO [tblBill] (
                [UUID], [CodeTp], [Code], [CodeExt],
                [DateDue], [DateBill], [DatePayed],
                [DateValidFrom], [DateValidTo],
                [ReplacementUUID],
                [CurrencyTpCode], [CurrencyCode],
                [Status],
                [AmountNet], [AmountTotal], [AmountDiscount],
                [TaxAnalysis],
                [Terms], [Note],
                [PaymentReference],
                [SubjectType], [SubjectId],
                [ThirdpartyType], [ThirdpartyId],
                [DateCreated], [DateUpdated],
                [UserCreatedUUID], [UserUpdatedUUID],
                [Version], [isDeleted], [Json_ext]
            )
            SELECT
                i.[UUID],
                i.[CodeTp],
                CASE
                    WHEN i.[Code] IS NULL OR i.[Code] = ''
                        THEN 'BIL-' + RIGHT(CONVERT(VARCHAR(4), YEAR(GETDATE())), 2) + '-'
                             + RIGHT('0000000000' + CAST(NEXT VALUE FOR bill_code_seq AS VARCHAR(20)), 10)
                    ELSE i.[Code]
                END,
                i.[CodeExt],
                i.[DateDue],
                i.[DateBill],
                i.[DatePayed],
                i.[DateValidFrom],
                i.[DateValidTo],
                i.[ReplacementUUID],
                i.[CurrencyTpCode],
                i.[CurrencyCode],
                i.[Status],
                i.[AmountNet],
                i.[AmountTotal],
                i.[AmountDiscount],
                i.[TaxAnalysis],
                i.[Terms],
                i.[Note],
                i.[PaymentReference],
                i.[SubjectType],
                i.[SubjectId],
                i.[ThirdpartyType],
                i.[ThirdpartyId],
                i.[DateCreated],
                i.[DateUpdated],
                i.[UserCreatedUUID],
                i.[UserUpdatedUUID],
                i.[Version],
                i.[isDeleted],
                i.[Json_ext]
            FROM inserted i;
        END
    """)


def _mssql_reverse(schema_editor):
    schema_editor.execute("""
        IF OBJECT_ID('bill_code_trigger', 'TR') IS NOT NULL
            DROP TRIGGER [bill_code_trigger];
    """)
    schema_editor.execute("""
        IF OBJECT_ID('bill_code_seq', 'SO') IS NOT NULL
            DROP SEQUENCE [bill_code_seq];
    """)


def apply_bill_code_trigger(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'postgresql':
        _pg_apply(schema_editor)
    elif vendor == 'microsoft':
        _mssql_apply(schema_editor)
    else:
        raise RuntimeError(
            f"Unsupported DB vendor '{vendor}' for bill code trigger migration; "
            "only 'postgresql' and 'microsoft' are supported."
        )


def reverse_bill_code_trigger(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'postgresql':
        _pg_reverse(schema_editor)
    elif vendor == 'microsoft':
        _mssql_reverse(schema_editor)
    else:
        raise RuntimeError(
            f"Unsupported DB vendor '{vendor}' for bill code trigger reverse migration; "
            "only 'postgresql' and 'microsoft' are supported."
        )


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0013_alter_bill_code_ext_alter_bill_code_tp_and_more'),
    ]

    operations = [
        migrations.RunPython(apply_bill_code_trigger, reverse_bill_code_trigger),
    ]
