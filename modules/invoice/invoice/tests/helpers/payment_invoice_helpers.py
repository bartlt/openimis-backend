from django.contrib.contenttypes.models import ContentType

from core.forms import User
from invoice.models import PaymentInvoice, DetailPaymentInvoice
from invoice.tests.helpers import create_test_invoice, create_test_invoice_line_item
from invoice.tests.helpers.default_test_data import DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD, \
    DEFAULT_TEST_DETAIL_PAYMENT_INVOICE_PAYLOAD


def create_test_payment_invoice_without_details(invoice=None, user=None, **custom_props):
    invoice = invoice or create_test_invoice()
    invoice_item = create_test_invoice_line_item(invoice=invoice)
    user = user or __get_or_create_user()

    payload = DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD.copy()
    payload.update(**custom_props)

    payment = PaymentInvoice(**payload)
    payment.save(username=user.username)

    return payment, invoice, invoice_item


def create_test_payment_invoice_with_details(invoice=None, user=None, **custom_props):
    invoice = invoice or create_test_invoice()
    create_test_invoice_line_item(invoice=invoice)
    user = user or __get_or_create_user()

    payload = DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD.copy()
    payload.update(**custom_props)

    payment = PaymentInvoice(**payload)
    payment.save(username=user.username)

    payload_detail = DEFAULT_TEST_DETAIL_PAYMENT_INVOICE_PAYLOAD.copy()
    payload_detail['subject'] = invoice
    payload_detail['subject_type'] = ContentType.objects.get_for_model(invoice)
    payload_detail.update(**custom_props)
    payment_detail = DetailPaymentInvoice(**payload_detail)
    payment_detail.payment = payment
    payment_detail.save(username=user.username)
    return payment


def __get_or_create_user():
    user = User.objects.filter(username='admin_invoice').first()
    if not user:
        user = User.objects.create_superuser(username='admin_invoice', password='S\/pe®Pąßw0rd™')
    return user
