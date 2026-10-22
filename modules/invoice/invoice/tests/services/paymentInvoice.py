from datetime import date
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.test import TestCase

from contract.tests.helpers import create_test_contract
from core.forms import User
from insuree.test_helpers import create_test_insuree
from invoice.models import Invoice, PaymentInvoice, DetailPaymentInvoice
from invoice.services.paymentInvoice import PaymentInvoiceService
from invoice.tests.helpers import (
    create_test_invoice,
    create_test_invoice_line_item,
    DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD,
    DEFAULT_TEST_DETAIL_PAYMENT_INVOICE_PAYLOAD
)
from invoice.validation.paymentInvoice import PaymentInvoiceModelValidation
from product.test_helpers import create_test_product
from policy.test_helpers import create_test_policy
from policyholder.tests.helpers import create_test_policy_holder


class ServiceTestPaymentInvoice(TestCase):
    BASE_EXPECTED_SUCCESS_RESPONSE = {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": {
            'status': 1,
            'label': 'test label',
            'code_tp': 'PAY_CODE',
            'code_receipt': 'PAY_CODE_RCP',
            'fees': 12.0,
            'amount_received': 91.50,
            'date_payment': str(date(2022, 4, 11))
        },
    }

    @classmethod
    def setUpClass(cls):
        super(ServiceTestPaymentInvoice, cls).setUpClass()
        cls.maxDiff = None
        if not User.objects.filter(username='admin_invoice').exists():
            User.objects.create_superuser(username='admin_invoice', password='S\/pe®Pąßw0rd™')

        cls.user = User.objects.filter(username='admin_invoice').first()
        cls.payment_invoice_service = PaymentInvoiceService(cls.user)

        cls.policy_holder = create_test_policy_holder()
        cls.contract = create_test_contract(cls.policy_holder)
        cls.insuree = create_test_insuree(with_family=True)
        cls.product = create_test_product("TestC0d3", custom_props={"insurance_period": 12})
        cls.policy = create_test_policy(
            product=cls.product,
            insuree=cls.insuree
        )

        cls.invoice = create_test_invoice(cls.contract, cls.insuree)
        cls.invoice_line_item = \
            create_test_invoice_line_item(invoice=cls.invoice, line_item=cls.policy, user=cls.user)

    def test_ref_received(self):
        with transaction.atomic():
            payment, payment_detail = self._create_payment(
                DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD,
                DEFAULT_TEST_DETAIL_PAYMENT_INVOICE_PAYLOAD
            )
            out = self.payment_invoice_service.ref_received(payment, 'code_ext1')
            expected = self.BASE_EXPECTED_SUCCESS_RESPONSE.copy()
            expected['data']['code_ext'] = 'code_ext1'
            payment_invoice = PaymentInvoice.objects.filter(code_ext=payment.code_ext).first()
            self.assertEqual(payment_invoice.code_ext, expected['data']['code_ext'])
            DetailPaymentInvoice.objects.filter(payment__code_ext=payment.code_ext).delete()
            PaymentInvoice.objects.filter(code_ext=payment.code_ext).delete()

    def test_payment_received(self):
        with transaction.atomic():
            payment, payment_detail = self._create_payment(
                DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD,
                DEFAULT_TEST_DETAIL_PAYMENT_INVOICE_PAYLOAD
            )
            self.payment_invoice_service.payment_received(
                payment,
                DetailPaymentInvoice.DetailPaymentStatus.ACCEPTED
            )
            detail_payment_invoice = DetailPaymentInvoice.objects.filter(payment__code_ext=payment.code_ext).first()
            self.assertEqual(detail_payment_invoice.subject.status, Invoice.Status.PAID)
            self.assertEqual(detail_payment_invoice.status, DetailPaymentInvoice.DetailPaymentStatus.ACCEPTED)
            DetailPaymentInvoice.objects.filter(payment__code_ext=payment.code_ext).delete()
            PaymentInvoice.objects.filter(code_ext=payment.code_ext).delete()

    def test_payment_received_invalid_amount(self):
        with transaction.atomic():
            payload = DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD.copy()
            payload['amount_received'] = 2.0
            payment, payment_detail = self._create_payment(
                payload,
                DEFAULT_TEST_DETAIL_PAYMENT_INVOICE_PAYLOAD
            )
            out = self.payment_invoice_service.payment_received(
                payment,
                DetailPaymentInvoice.DetailPaymentStatus.ACCEPTED
            )
            detail = [str(PaymentInvoiceModelValidation.AMOUNT_PAYED_NOT_MATCHING_ITEMS \
                          % {'payment_invoice': payment, 'expected': 91.5, 'payed': 2.0})]
            message = 'Failed to payment_received PaymentInvoice'
            self._assert_output_invalid(out, message, detail)
            DetailPaymentInvoice.objects.filter(payment__code_ext=payment.code_ext).delete()
            PaymentInvoice.objects.filter(code_ext=payment.code_ext).delete()

    def test_payment_refunded(self):
        with transaction.atomic():
            payment, payment_detail = self._create_payment(
                DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD,
                DEFAULT_TEST_DETAIL_PAYMENT_INVOICE_PAYLOAD
            )
            self.payment_invoice_service.payment_refunded(payment)
            detail_payment_invoice = DetailPaymentInvoice.objects.filter(payment__code_ext=payment.code_ext).first()
            self.assertEqual(detail_payment_invoice.subject.status, Invoice.Status.SUSPENDED)
            self.assertEqual(detail_payment_invoice.status, DetailPaymentInvoice.DetailPaymentStatus.REFUNDED)
            DetailPaymentInvoice.objects.filter(payment__code_ext=payment.code_ext).delete()
            PaymentInvoice.objects.filter(code_ext=payment.code_ext).delete()

    def test_payment_cancelled(self):
        with transaction.atomic():
            payment, payment_detail = self._create_payment(
                DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD,
                DEFAULT_TEST_DETAIL_PAYMENT_INVOICE_PAYLOAD
            )
            self.payment_invoice_service.payment_cancelled(payment)
            detail_payment_invoice = DetailPaymentInvoice.objects.filter(payment__code_ext=payment.code_ext).first()
            self.assertEqual(detail_payment_invoice.subject.status, Invoice.Status.SUSPENDED)
            self.assertEqual(detail_payment_invoice.status, DetailPaymentInvoice.DetailPaymentStatus.CANCELLED)
            DetailPaymentInvoice.objects.filter(payment__code_ext=payment.code_ext).delete()
            PaymentInvoice.objects.filter(code_ext=payment.code_ext).delete()

    def _create_payment(self, payment, payment_detail):
        payment = PaymentInvoice(**payment)
        payment.invoice = self.invoice
        payment.save(user=self.user)
        payload_detail = DEFAULT_TEST_DETAIL_PAYMENT_INVOICE_PAYLOAD.copy()
        payload_detail['subject'] = self.invoice
        payload_detail['subject_type'] = ContentType.objects.get_for_model(self.invoice)
        payment_detail = DetailPaymentInvoice(**payload_detail)
        payment_detail.payment = payment
        payment_detail.save(user=self.user)
        return payment, payment_detail

    def _assert_output_valid(self, out, payment, expected):
        expected['data']['id'] = str(payment.id)
        out['data'] = {k: v for k, v in out['data'].items() if k in expected['data'].keys()}
        self.assertDictEqual(out, expected)

    def _assert_output_invalid(self, out, message, detail):
        expected = {
            'success': False,
            'message': message,
            'detail': str(detail).replace('\'', '').replace('\"', ''),
            'data': ''
        }
        out['detail'] = out['detail'].replace('\'', '').replace('\"', '')
        self.assertDictEqual(out, expected)
