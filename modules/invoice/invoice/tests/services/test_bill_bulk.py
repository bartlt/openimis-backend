import uuid
from decimal import Decimal
from django.test import TestCase
from core.test_helpers import LogInHelper
from invoice.models import Bill, BillItem
from invoice.services import BillService


class BillBulkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = LogInHelper().get_or_create_user_api(username='admin_bulk')

    def test_bulk_create_bills_success(self):
        """Verify that bulk_create_bills correctly persists multiple Bill instances."""
        bill_instances = []

        for i in range(5):
            bill_instances.append(Bill(
                id=uuid.uuid4(),
                subject_type=None,
                subject_id=None,
                code=f"BULK_BILL_{i}",
                status=Bill.Status.VALIDATED,
                user_created=self.user,
                user_updated=self.user,
                version=1
            ))

        created_bills = BillService.bulk_create_bills(bill_instances)
        self.assertEqual(len(created_bills), 5)
        self.assertEqual(Bill.objects.filter(code__startswith="BULK_BILL_").count(), 5)

    def test_bulk_create_bill_items_success(self):
        """Verify that bulk_create_bill_items correctly persists multiple BillItem instances."""
        bill = Bill(
            code="PARENT_BILL",
            subject_type=None,
            subject_id=None,
            status=Bill.Status.VALIDATED,
            user_created=self.user,
            user_updated=self.user,
            version=1
        )
        bill.save(username=self.user.username)

        item_instances = []
        for i in range(10):
            item_instances.append(BillItem(
                id=uuid.uuid4(),
                bill=bill,
                code=f"ITEM_{i}",
                amount_total=Decimal('100.00'),
                user_created=self.user,
                user_updated=self.user,
                version=1
            ))

        created_items = BillService.bulk_create_bill_items(item_instances)
        self.assertEqual(len(created_items), 10)
        self.assertEqual(BillItem.objects.filter(bill=bill).count(), 10)

    def test_bulk_create_bills_with_empty_code_gets_db_assigned(self):
        """Verify that bulk-created Bills with empty code get a DB-trigger-assigned code."""
        bill_instances = [
            Bill(
                id=uuid.uuid4(),
                subject_type=None,
                subject_id=None,
                code='',
                status=Bill.Status.VALIDATED,
                user_created=self.user,
                user_updated=self.user,
                version=1
            )
            for _ in range(3)
        ]

        created_bills = BillService.bulk_create_bills(bill_instances)
        self.assertEqual(len(created_bills), 3)
        for bill in created_bills:
            self.assertTrue(
                bill.code.startswith('BIL-'),
                f"Expected DB-assigned BIL- prefix, got: {bill.code!r}"
            )
        # Codes must be unique
        codes = [b.code for b in created_bills]
        self.assertEqual(len(codes), len(set(codes)), "DB-assigned codes must be unique")
