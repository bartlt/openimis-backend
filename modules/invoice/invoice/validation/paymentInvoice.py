from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from core.validation import BaseModelValidation, UniqueCodeValidationMixin, ObjectExistsValidationMixin
from invoice.models import PaymentInvoice
from invoice.utils import resolve_payment_details
from invoice.validation.paymentStatusValidation import InvoicePaymentReceiveStatusValidator, \
    InvoicePaymentRefundStatusValidator, InvoicePaymentCancelStatusValidator


class PaymentInvoiceModelValidation(BaseModelValidation, UniqueCodeValidationMixin, ObjectExistsValidationMixin):
    OBJECT_TYPE = PaymentInvoice

    AMOUNT_PAYED_NOT_MATCHING_ITEMS = _(
        "Amount payed for payment_invoice %(payment_invoice)s is not matching amount total. "
        "Expected: %(expected).2f, Payed: %(payed).2f"
    )

    INVALID_AMOUNT_TOTAL = _("Not all payment_invoice line items for payment_invoice %(payment_invoice)s have a amount total attached. "
                             "It's not possible to validate payment. ")

    @classmethod
    def validate_create(cls, user, **data):
        cls.validate_unique_code_name(data.get('code_ext', None))

    @classmethod
    def validate_ref_received(cls, user, payment, payment_ref):
        excluded = payment.id if payment else None
        cls.validate_unique_code_name(payment_ref, excluded_id=excluded, code_key='code_ext')

    @classmethod
    def validate_update(cls, user, **data):
        cls.validate_object_exists(data.get('id', None))
        code = data.get('code_ext', None)
        id_ = data.get('id', None)

        if code:
            cls.validate_unique_code_name(code, id_)

    @classmethod
    def validate_receive_payment(cls, user, invoice_payment):
        cls._validate_payment_match_items(user, invoice_payment)

    @classmethod
    def validate_refund_payment(cls, user, invoice_payment):
        InvoicePaymentRefundStatusValidator(invoice_payment)()

    @classmethod
    def validate_cancel_payment(cls, user, invoice_payment):
        InvoicePaymentCancelStatusValidator(invoice_payment)()

    @classmethod
    def _validate_payment_match_items(cls, user, payment_invoice: PaymentInvoice):
        invoices, bills = resolve_payment_details(payment_invoice)
        line_items = []
        for invoice in invoices:
            line_items += [x.amount_total for x in invoice.line_items.all()]
        for bill in bills:
            line_items += [x.amount_total for x in bill.line_items_bill.all()]
        if len(line_items) == 0:
            raise ValidationError(cls.INVALID_AMOUNT_TOTAL % {
                'payment_invoice': payment_invoice
            })
        if None in line_items:
            raise ValidationError(cls.INVALID_AMOUNT_TOTAL % {
                'payment_invoice': payment_invoice
            })
        expected_amount = sum(line_items)
        if expected_amount != payment_invoice.amount_received:
            raise ValidationError(cls.AMOUNT_PAYED_NOT_MATCHING_ITEMS % {
                'payment_invoice': payment_invoice,
                'expected': expected_amount,
                'payed': payment_invoice.amount_received
            })
