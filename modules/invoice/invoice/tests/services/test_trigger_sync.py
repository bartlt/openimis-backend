import uuid
from django.db import connection
from django.test import TestCase
from core.test_helpers import LogInHelper
from invoice.models import Bill
from invoice.trigger_sync import (
    parse_pattern,
    validate_pattern,
    pattern_to_pg_expr,
    pattern_to_mssql_expr,
    sync_trigger,
    DEFAULT_BILL_CODE_PATTERN,
    _get_model_columns,
)


class PatternParsingTests(TestCase):
    """Tests for code pattern parsing and SQL generation."""

    def test_parse_default_pattern(self):
        segments = parse_pattern("BIL-[YY]-[SEQ:10]")
        self.assertEqual(segments, [
            ('literal', 'BIL-'),
            ('token', '[YY]'),
            ('literal', '-'),
            ('token', '[SEQ:10]'),
        ])

    def test_parse_custom_pattern(self):
        segments = parse_pattern("CUSTOM-[YYYY][MM]-[SEQ:8]")
        self.assertEqual(segments, [
            ('literal', 'CUSTOM-'),
            ('token', '[YYYY]'),
            ('token', '[MM]'),
            ('literal', '-'),
            ('token', '[SEQ:8]'),
        ])

    def test_parse_seq_only(self):
        segments = parse_pattern("[SEQ:12]")
        self.assertEqual(segments, [('token', '[SEQ:12]')])

    def test_parse_seq_no_padding(self):
        segments = parse_pattern("X-[SEQ]")
        self.assertEqual(segments, [
            ('literal', 'X-'),
            ('token', '[SEQ]'),
        ])

    def test_parse_all_tokens(self):
        segments = parse_pattern("[YY][YYYY][MM][SEQ:6]")
        tokens = [v for t, v in segments if t == 'token']
        self.assertEqual(tokens, ['[YY]', '[YYYY]', '[MM]', '[SEQ:6]'])

    def test_validate_pattern_valid(self):
        self.assertTrue(validate_pattern("BIL-[YY]-[SEQ:10]"))
        self.assertTrue(validate_pattern("CUSTOM-[YYYY][MM]-[SEQ:8]"))
        self.assertTrue(validate_pattern("[SEQ:12]"))
        self.assertTrue(validate_pattern("INV/[YYYY]/[SEQ:6]"))

    def test_validate_pattern_no_seq_token(self):
        with self.assertRaises(ValueError):
            validate_pattern("NO-SEQ-TOKEN")

    def test_validate_pattern_multiple_seq_tokens(self):
        with self.assertRaises(ValueError):
            validate_pattern("[SEQ:6]-[SEQ:4]")

    def test_validate_pattern_unsafe_literal(self):
        with self.assertRaises(ValueError):
            validate_pattern("'; DROP TABLE x; --[SEQ:10]")

    def test_pg_expr_default_pattern(self):
        expr = pattern_to_pg_expr("BIL-[YY]-[SEQ:10]", "bill_code_seq")
        self.assertIn("to_char(now(), 'YY')", expr)
        self.assertIn("nextval('bill_code_seq')", expr)
        self.assertIn("lpad(", expr)

    def test_pg_expr_custom_pattern(self):
        expr = pattern_to_pg_expr("INV/[YYYY]/[SEQ:6]", "my_seq")
        self.assertIn("'INV/'", expr)
        self.assertIn("to_char(now(), 'YYYY')", expr)
        self.assertIn("lpad(nextval('my_seq')::text, 6, '0')", expr)

    def test_mssql_expr_default_pattern(self):
        expr = pattern_to_mssql_expr("BIL-[YY]-[SEQ:10]", "bill_code_seq")
        self.assertIn("YEAR(GETDATE())", expr)
        self.assertIn("NEXT VALUE FOR bill_code_seq", expr)
        self.assertIn("RIGHT(", expr)

    def test_mssql_expr_custom_pattern(self):
        expr = pattern_to_mssql_expr("CUSTOM-[YYYY][MM]-[SEQ:8]", "my_seq")
        self.assertIn("'CUSTOM-'", expr)
        self.assertIn("YEAR(GETDATE())", expr)
        self.assertIn("MONTH(GETDATE())", expr)
        self.assertIn("NEXT VALUE FOR my_seq", expr)


class ModelColumnIntrospectionTests(TestCase):
    """Tests for model column extraction used by MSSQL trigger sync."""

    def test_bill_columns_include_expected(self):
        columns = _get_model_columns(Bill)
        # Core columns from GenericInvoice + Bill
        for expected in ('UUID', 'Code', 'Status', 'SubjectType', 'SubjectId'):
            self.assertIn(expected, columns, f"Expected column {expected} in Bill model")

    def test_bill_columns_include_replacement_uuid(self):
        columns = _get_model_columns(Bill)
        self.assertIn('ReplacementUUID', columns, "ReplacementUUID must be in Bill columns")

    def test_bill_columns_no_duplicates(self):
        columns = list(f.column for f in Bill._meta.concrete_fields)
        self.assertEqual(len(columns), len(set(columns)), "Duplicate column names detected")


class TriggerSyncTests(TestCase):
    """Tests for trigger sync detection and application."""

    @classmethod
    def setUpTestData(cls):
        cls.user = LogInHelper().get_or_create_user_api(username='trigger_sync_test')

    def test_sync_detects_in_sync(self):
        """Default pattern should be in sync with the current trigger."""
        updated = sync_trigger(
            model=Bill,
            sequence_name='bill_code_seq',
            trigger_name='bill_code_trigger',
            code_column='Code',
            pattern=DEFAULT_BILL_CODE_PATTERN,
            pg_function_name='set_bill_code',
            dry_run=True,
        )
        if connection.vendor in ('postgresql', 'microsoft'):
            self.assertFalse(updated, "Default pattern should already be in sync")
        else:
            self.assertIsNone(updated, "Unsupported vendor should return None")

    def test_sync_detects_pattern_change(self):
        """A different pattern should be detected as needing update."""
        updated = sync_trigger(
            model=Bill,
            sequence_name='bill_code_seq',
            trigger_name='bill_code_trigger',
            code_column='Code',
            pattern='CHANGED-[YYYY]-[SEQ:6]',
            pg_function_name='set_bill_code',
            dry_run=True,
        )
        if connection.vendor in ('postgresql', 'microsoft'):
            self.assertTrue(updated, "Changed pattern should be detected as needing update")

    def test_sync_applies_custom_pattern(self):
        """Apply a custom pattern, verify it generates correct codes, then restore."""
        if connection.vendor not in ('postgresql', 'microsoft'):
            self.skipTest("Trigger sync only works on PostgreSQL and MSSQL")

        custom_pattern = 'TST-[YYYY][MM]-[SEQ:6]'

        # Apply custom
        sync_trigger(
            model=Bill,
            sequence_name='bill_code_seq',
            trigger_name='bill_code_trigger',
            code_column='Code',
            pattern=custom_pattern,
            pg_function_name='set_bill_code',
        )

        try:
            # Create a bill with empty code
            bill = Bill(
                id=uuid.uuid4(),
                subject_type=None, subject_id=None, code='',
                status=Bill.Status.VALIDATED,
                user_created=self.user, user_updated=self.user, version=1,
            )
            bill.save(username=self.user.username)
            bill.refresh_from_db()
            self.assertTrue(
                bill.code.startswith('TST-'),
                f"Expected TST- prefix from custom pattern, got: {bill.code!r}"
            )

            # Verify it's now detected as in sync
            in_sync = sync_trigger(
                model=Bill,
                sequence_name='bill_code_seq',
                trigger_name='bill_code_trigger',
                code_column='Code',
                pattern=custom_pattern,
                pg_function_name='set_bill_code',
                dry_run=True,
            )
            self.assertFalse(in_sync, "Custom pattern should be in sync after applying")
        finally:
            # Restore default
            sync_trigger(
                model=Bill,
                sequence_name='bill_code_seq',
                trigger_name='bill_code_trigger',
                code_column='Code',
                pattern=DEFAULT_BILL_CODE_PATTERN,
                pg_function_name='set_bill_code',
            )
            Bill.objects.filter(id=bill.id).delete()

    def test_sync_preserves_explicit_codes(self):
        """Trigger should not overwrite explicitly provided codes regardless of pattern."""
        if connection.vendor not in ('postgresql', 'microsoft'):
            self.skipTest("Trigger sync only works on PostgreSQL and MSSQL")

        bill = Bill(
            id=uuid.uuid4(),
            subject_type=None, subject_id=None, code='EXPLICIT-CODE',
            status=Bill.Status.VALIDATED,
            user_created=self.user, user_updated=self.user, version=1,
        )
        bill.save(username=self.user.username)
        bill.refresh_from_db()
        self.assertEqual(bill.code, 'EXPLICIT-CODE', "Explicit code must not be overwritten")
        Bill.objects.filter(id=bill.id).delete()

    def test_bulk_create_history_records_have_db_assigned_codes(self):
        """Verify that history records are patched with DB-assigned codes after bulk create."""
        bills = [
            Bill(
                id=uuid.uuid4(),
                subject_type=None, subject_id=None, code='',
                status=Bill.Status.VALIDATED,
                user_created=self.user, user_updated=self.user, version=1,
            )
            for _ in range(3)
        ]
        from invoice.services import BillService
        created = BillService.bulk_create_bills(bills)

        for bill in created:
            self.assertTrue(bill.code, "Bill code should be populated after bulk create")
            # Check history record has the same code
            history = Bill.history.filter(id=bill.id, history_type='+').first()
            self.assertIsNotNone(history, f"Expected history record for Bill {bill.id}")
            self.assertEqual(
                history.code, bill.code,
                f"History code {history.code!r} should match bill code {bill.code!r}"
                )
