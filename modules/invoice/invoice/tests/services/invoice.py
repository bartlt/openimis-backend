import json
from datetime import date, datetime, timedelta

from django.db import transaction
from django.test import TestCase

from contract.tests.helpers import create_test_contract
from core.forms import User
from core.test_helpers import compare_dicts
from insuree.test_helpers import create_test_insuree
from invoice.models import Invoice, InvoiceLineItem, InvoicePayment
from invoice.services import InvoiceService
from invoice.tests.helpers import create_test_invoice_line_item
from invoice.validation import TaxAnalysisFormatValidationMixin, InvoiceItemStatus
from policy.test_helpers import create_test_policy
from policyholder.tests.helpers import create_test_policy_holder
from product.test_helpers import create_test_product


class ServiceTestInvoice(TestCase):
    BASE_TEST_INVOICE_PAYLOAD = {
        'subject_type': 'contract',
        'subject_id': None,
        'thirdparty_type': 'insuree',
        'thirdparty_id': None,
        'code': 'INVOICE_CODE',
        'code_tp': 'INVOICE_CODE_TP',
        'code_ext': 'INVOICE_CODE_EXT',
        'date_due': date(2021, 9, 13),
        'date_invoice': date(2021, 9, 11),
        'date_payed': date(2021, 9, 12),
        'amount_discount': 20.1,
        'amount_net': 20.1,
        'tax_analysis': {'lines': [{'code': 'c', 'label': 'l', 'base': '0.1', 'amount': '2.01'}], 'total': '2.01'},
        'amount_total': 20.1,
        'status': 0,  # Draft
        'note': 'NOTE',
        'terms': 'TERMS',
        'payment_reference': 'payment reference'
    }

    BASE_TEST_UPDATE_INVOICE_PAYLOAD = {
        'id': None,
        'thirdparty_type': 'policyholder',
        'thirdparty_id': None,
        'code': 'INVOICE_CODE_2',
        'code_tp': 'INVOICE_CODE_TP_2',
        'code_ext': 'INVOICE_CODE_EXT_2',
        'date_due': date(2021, 10, 13),
        'date_invoice': date(2021, 10, 11),
        'date_payed': date(2021, 10, 12),
        'amount_discount': 22.1,
        'amount_net': 22.1,
        'tax_analysis': {'lines': [{'code': 'c', 'label': 'l', 'base': '0.1', 'amount': '2.21'}], 'total': '2.21'},
        'amount_total': 22.1,
        'status': 1,  # Draft
        'note': 'NOTE_2',
        'terms': 'TERMS_2',
        'payment_reference': 'payment reference 2'
    }

    BASE_EXPECTED_CREATE_RESPONSE = {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": {
            'subject_type': None,
            'subject_id': None,
            'thirdparty_type': None,
            'thirdparty_id': None,
            'code': 'INVOICE_CODE',
            'code_tp': 'INVOICE_CODE_TP',
            'code_ext': 'INVOICE_CODE_EXT',
            'date_due': '2021-09-13',
            'date_invoice': '2021-09-11',
            'date_payed': '2021-09-12',
            'amount_discount': 20.1,
            'amount_net': 20.1,
            'tax_analysis': {'lines': [{'code': 'c', 'label': 'l', 'base': '0.1', 'amount': '2.01'}], 'total': '2.01'},
            'amount_total': 20.1,
            'status': 0,  # Draft
            'note': 'NOTE',
            'terms': 'TERMS',
            'payment_reference': 'payment reference',
            'currency_code': 'USD'
        },
    }

    BASE_EXPECTED_UPDATE_RESPONSE = {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": {
            'thirdparty_type': None,
            'thirdparty_id': None,
            'code': 'INVOICE_CODE_2',
            'code_tp': 'INVOICE_CODE_TP_2',
            'code_ext': 'INVOICE_CODE_EXT_2',
            'date_due': '2021-10-13',
            'date_invoice': '2021-10-11',
            'date_payed': '2021-10-12',
            'amount_discount': 22.1,
            'amount_net': 22.1,
            'tax_analysis': {'lines': [{'code': 'c', 'label': 'l', 'base': '0.1', 'amount': '2.21'}], 'total': '2.21'},
            'amount_total': 22.1,
            'status': 1,  # Draft
            'note': 'NOTE_2',
            'terms': 'TERMS_2',
            'payment_reference': 'payment reference 2'
        },
    }

    @classmethod
    def setUpClass(cls):
        super(ServiceTestInvoice, cls).setUpClass()
        if not User.objects.filter(username='admin_invoice').exists():
            User.objects.create_superuser(username='admin_invoice', password='S\/pe®Pąßw0rd™')

        InvoiceLineItem.objects \
            .filter(invoice__code=cls.BASE_TEST_INVOICE_PAYLOAD['code']).delete()
        InvoicePayment.objects \
            .filter(invoice__code=cls.BASE_TEST_INVOICE_PAYLOAD['code']).delete()
        Invoice.objects.filter(code=cls.BASE_TEST_INVOICE_PAYLOAD['code']).delete()

        cls.policy_holder = create_test_policy_holder()
        cls.contract = create_test_contract(cls.policy_holder)
        cls.user = User.objects.filter(username='admin_invoice').first()
        cls.insuree = create_test_insuree(with_family=True)
        cls.insuree_service = InvoiceService(cls.user)

        cls.BASE_TEST_INVOICE_PAYLOAD['subject'] = cls.contract
        cls.BASE_TEST_INVOICE_PAYLOAD['thirdparty'] = cls.insuree

        # Business model use PK of uuid type
        cls.BASE_EXPECTED_CREATE_RESPONSE['data']['subject_id'] = str(cls.contract.pk)
        cls.BASE_EXPECTED_CREATE_RESPONSE['data']['thirdparty_id'] = cls.insuree.pk

        cls.product = create_test_product("TestC0d4", custom_props={"insurance_period": 12})
        cls.policy = create_test_policy(
            product=cls.product,
            insuree=cls.insuree
        )

    def test_invoice_create(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYLOAD.copy()
            expected_response = self.BASE_EXPECTED_CREATE_RESPONSE.copy()
            response = self.insuree_service.create(payload)
            truncated_output = response
            truncated_output['data'] = {k: v for k, v in truncated_output['data'].items()
                                        if k in expected_response['data'].keys()}

            invoice = Invoice.objects.filter(code=payload['code']).first()
            expected_response['data']['subject_type'] = invoice.subject_type.id
            expected_response['data']['thirdparty_type'] = invoice.thirdparty_type.id

            self.assertTrue(compare_dicts(expected_response, response))
            Invoice.objects.filter(code=payload['code']).delete()

    def test_invoice_update(self):
        with transaction.atomic():
            create_payload = self.BASE_TEST_INVOICE_PAYLOAD.copy()
            update_payload = self.BASE_TEST_UPDATE_INVOICE_PAYLOAD.copy()
            expected_response = self.BASE_EXPECTED_UPDATE_RESPONSE.copy()

            self.insuree_service.create(create_payload)
            update_payload['id'] = \
                Invoice.objects.filter(code=create_payload['code']).first().id

            response = self.insuree_service.update(update_payload)

            truncated_output = response
            truncated_output['data'] = {k: v for k, v in truncated_output['data'].items()
                                        if k in expected_response['data'].keys()}

            invoice = Invoice.objects.filter(code=update_payload['code']).first()

            expected_response['data']['thirdparty_type'] = invoice.thirdparty_type.id
            self.assertTrue(compare_dicts(expected_response, response))

            Invoice.objects.filter(code=update_payload['code']).delete()

    def test_invoice_delete(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYLOAD.copy()
            expected_response = {
                "success": True,
                "message": "Ok",
                "detail": "",
            }

            response = self.insuree_service.create(payload)
            response = self.insuree_service.delete(response['data'])
            self.assertDictEqual(expected_response, response)
            Invoice.objects.filter(code=payload['code']).delete()

    def test_invoice_code_duplicate(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYLOAD.copy()
            _ = self.insuree_service.create(payload)
            response = self.insuree_service.create(payload)
            expected_response = {
                "success": False,
                "message": "Failed to create Invoice",
                "detail": "['Object code INVOICE_CODE is not unique.']",
                "data": ''
            }
            self.assertDictEqual(expected_response, response)
            Invoice.objects.filter(code=payload['code']).delete()

    def test_invoice_invalid_tax_analysis_format(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYLOAD.copy()
            payload['tax_analysis'] = {'total': '2.01'}
            response = self.insuree_service.create(payload)
            expected_response = {
                "success": False,
                "message": "Failed to create Invoice",
                "detail": json.dumps([TaxAnalysisFormatValidationMixin.INVALID_TAX_ANALYSIS_JSON_FORMAT_NO_KEYS]),
                "data": ''
            }
            self.assertDictEqual(expected_response, response)
            Invoice.objects.filter(code=payload['code']).delete()

    def test_invoice_match_items_subject_id(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYLOAD.copy()
            response = self.insuree_service.create(payload)
            invoice = Invoice.objects.filter(code=payload['code']).get()
            invoice_line_item = create_test_invoice_line_item(invoice=invoice, line_item=self.policy, user=self.user)

            output = self.insuree_service.invoice_match_items(invoice)
            expected_output = {
                'subject': InvoiceItemStatus.VALID,
                'line_items': {invoice_line_item: InvoiceItemStatus.VALID}
            }

            self.assertDictEqual(output, expected_output)
            InvoiceLineItem.objects.filter(id=invoice_line_item.id).delete()
            Invoice.objects.filter(code=payload['code']).delete()

    def test_invoice_match_items_no_subject_valid_line_item(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYLOAD.copy()
            response = self.insuree_service.create(payload)
            invoice = Invoice.objects.filter(code=payload['code']).get()
            invoice.subject = None
            invoice.save(user=self.user)
            invoice_line_item = create_test_invoice_line_item(invoice=invoice, line_item=self.policy, user=self.user)

            output = self.insuree_service.invoice_match_items(invoice)
            expected_output = {
                'subject': InvoiceItemStatus.NO_ITEM,
                'line_items': {invoice_line_item: InvoiceItemStatus.VALID}
            }
            self.assertDictEqual(output, expected_output)
            InvoiceLineItem.objects.filter(id=invoice_line_item.id).delete()
            Invoice.objects.filter(code=payload['code']).delete()

    def test_invoice_match_items_no_subject_id_invalid_no_line_item(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYLOAD.copy()
            response = self.insuree_service.create(payload)
            invoice = Invoice.objects.filter(code=payload['code']).get()
            invoice_line_item = create_test_invoice_line_item(invoice=invoice, line_item=self.policy, user=self.user)
            invoice.subject = None
            invoice.save(user=self.user)
            invoice_line_item.line = None
            invoice_line_item.save(user=self.user)

            output = self.insuree_service.invoice_match_items(invoice)
            expected_output = {
                'subject': InvoiceItemStatus.NO_ITEM,
                'line_items': {invoice_line_item: InvoiceItemStatus.NO_ITEM}
            }
            self.assertDictEqual(output, expected_output)
            InvoiceLineItem.objects.filter(id=invoice_line_item.id).delete()
            Invoice.objects.filter(code=payload['code']).delete()

    def test_invoice_match_items_subject_id_invalid_outdated_item(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYLOAD.copy()
            response = self.insuree_service.create(payload)
            invoice = Invoice.objects.filter(code=payload['code']).get()
            invoice_line_item = create_test_invoice_line_item(invoice=invoice, line_item=self.policy, user=self.user)
            invoice_line_item.line.validity_to = datetime.now() - timedelta(days=1)
            invoice_line_item.line.save()

            output = self.insuree_service.invoice_match_items(invoice)
            expected_output = {
                'subject': InvoiceItemStatus.VALID,
                'line_items': {invoice_line_item: InvoiceItemStatus.INVALID_ITEM}
            }
            self.assertDictEqual(output, expected_output)
            InvoiceLineItem.objects.filter(id=invoice_line_item.id).delete()
            Invoice.objects.filter(code=payload['code']).delete()
