from django.db import transaction
from policy.test_helpers import create_test_policy
from product.test_helpers import create_test_product

from core.forms import User
from core.test_helpers import compare_dicts
from django.test import TestCase

from invoice.models import InvoiceLineItem
from contract.tests.helpers import create_test_contract
from policyholder.tests.helpers import create_test_policy_holder
from insuree.test_helpers import create_test_insuree

from invoice.services.invoiceLineItem import InvoiceLineItemService
from invoice.tests.helpers import create_test_invoice


class ServiceTestInvoiceLineItems(TestCase):
    BASE_TEST_INVOICE_LINE_ITEM_PAYLOAD = {
        'code': 'LineItem1',
        # 'line_type': None,
        # 'line_id': None,
        # 'invoiceId': None,
        'description': 'description_str',
        'details': '{"test_int": 1, "test_txt": "some_str"}',
        'ledger_account': 'account',
        'quantity': 10,
        'unit_price': 10.5,
        'discount': 15.5,
        'tax_rate': None,
        'tax_analysis': {'lines': [{'code': 'c', 'label': 'l', 'base': '0.1', 'amount': '2.00'}], 'total': '2.0'},
    }

    BASE_TEST_UPDATE_LINE_ITEM_PAYLOAD = {
        'code': 'LineItem2',
        'description': 'description_str2',
        'details': '{"test_int": 1, "test_txt": "some_str"}',
        'ledger_account': 'account2',
        'quantity': 12,
        'unit_price': 10,
        'discount': 20,
        'tax_rate': None,
        'tax_analysis': {'lines': [{'code': 'c', 'label': 'l', 'base': '0.1', 'amount': '1.00'}], 'total': '1.0'},
    }

    BASE_EXPECTED_CREATE_RESPONSE = {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": {
            'code': 'LineItem1',
            'line_type': None,
            'line_id': None,
            'invoice': None,
            'amount_total': 91.5,
            'amount_net': 89.5,
            'description': 'description_str',
            'details': {"test_int": 1, "test_txt": "some_str"},
            'ledger_account': 'account',
            'quantity': 10,
            'unit_price': 10.5,
            'discount': 15.5,
            'tax_rate': None,
            'tax_analysis': {'lines': [{'code': 'c', 'label': 'l', 'base': '0.1', 'amount': '2.00'}], 'total': '2.0'}
        },
    }

    BASE_EXPECTED_UPDATE_RESPONSE = {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": {
            'code': 'LineItem2',
            'amount_total': 101.0,
            'amount_net': 100.0,
            'description': 'description_str2',
            'details': {"test_int": 1, "test_txt": "some_str"},
            'ledger_account': 'account2',
            'quantity': 12,
            'unit_price': 10.0,
            'discount': 20.0,
            'tax_analysis': {'lines': [{'code': 'c', 'label': 'l', 'base': '0.1', 'amount': '1.00'}], 'total': '1.0'},
            'line_id': None,
            'line_type': None
        },
    }

    @classmethod
    def setUpClass(cls):
        super(ServiceTestInvoiceLineItems, cls).setUpClass()
        if not User.objects.filter(username='admin_invoice').exists():
            User.objects.create_superuser(username='admin_invoice', password='S\/pe®Pąßw0rd™')

        cls.policy_holder = create_test_policy_holder()
        cls.contract = create_test_contract(cls.policy_holder)
        cls.user = User.objects.filter(username='Admin').first()
        cls.insuree = create_test_insuree(with_family=True)
        cls.line_item_service = InvoiceLineItemService(cls.user)
        cls.invoice = create_test_invoice(cls.contract, cls.insuree)
        cls.product = create_test_product("TestC0d3", custom_props={"insurance_period": 12})
        cls.policy = create_test_policy(
            product=cls.product,
            insuree=cls.insuree
        )

        cls.BASE_TEST_INVOICE_LINE_ITEM_PAYLOAD['line'] = cls.policy
        cls.BASE_TEST_INVOICE_LINE_ITEM_PAYLOAD['invoice'] = cls.invoice

    def test_line_items_create(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_LINE_ITEM_PAYLOAD.copy()
            payload['invoice'] = self.invoice

            expected_response = self.BASE_EXPECTED_CREATE_RESPONSE.copy()
            expected_response['data']['invoice'] = str(self.invoice.pk)

            response = self.line_item_service.create(payload)

            truncated_output = response
            truncated_output['data'] = {k: v for k, v in truncated_output['data'].items()
                                        if k in expected_response['data'].keys()}

            line_item = InvoiceLineItem.objects.filter(code=payload['code']).first()
            expected_response['data']['line_type'] = line_item.line_type.id
            expected_response['data']['line_id'] = self.policy.pk

            self.assertTrue(compare_dicts(expected_response, response))
            InvoiceLineItem.objects.filter(code=payload['code']).delete()

    def test_line_items_update(self):
        self.maxDiff = None
        with transaction.atomic():
            create_payload = self.BASE_TEST_INVOICE_LINE_ITEM_PAYLOAD.copy()
            create_payload['invoice'] = self.invoice

            expected_response = self.BASE_EXPECTED_UPDATE_RESPONSE.copy()
            expected_response['data']['invoice'] = str(self.invoice.pk)

            self.line_item_service.create(create_payload)

            update_payload = self.BASE_TEST_UPDATE_LINE_ITEM_PAYLOAD.copy()
            update_payload['id'] = InvoiceLineItem.objects.filter(code=create_payload['code']).first().id

            response = self.line_item_service.update(update_payload)
            truncated_output = response
            truncated_output['data'] = {k: v for k, v in truncated_output['data'].items()
                                        if k in expected_response['data'].keys()}

            line_item = InvoiceLineItem.objects.filter(code=update_payload['code']).first()

            expected_response['data']['line_type'] = line_item.line_type.id
            expected_response['data']['line_id'] = str(self.policy.pk)

            self.assertTrue(compare_dicts(expected_response, response))
            InvoiceLineItem.objects.filter(code=update_payload['code']).delete()

    def test_line_items_delete(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_LINE_ITEM_PAYLOAD.copy()
            expected_response = {
                "success": True,
                "message": "Ok",
                "detail": "",
            }

            response = self.line_item_service.create(payload)
            response = self.line_item_service.delete(response['data'])
            self.assertDictEqual(expected_response, response)
            InvoiceLineItem.objects.filter(code=payload['code']).delete()
