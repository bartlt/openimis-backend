from django.core.exceptions import ValidationError

from invoice.models import InvoicePayment
from core.validation import BaseModelValidation, UniqueCodeValidationMixin, ObjectExistsValidationMixin
from django.utils.translation import gettext as _

from invoice.validation.paymentStatusValidation import InvoicePaymentReceiveStatusValidator, \
    InvoicePaymentRefundStatusValidator, InvoicePaymentCancelStatusValidator


class InvoicePaymentModelValidation(BaseModelValidation, UniqueCodeValidationMixin, ObjectExistsValidationMixin):
    OBJECT_TYPE = InvoicePayment

    AMOUNT_PAYED_NOT_MATCHING_ITEMS = _(
        "Amount payed for invoice %(invoice)s is not matching amount total. "
        "Expected: %(expected).2f, Payed: %(payed).2f"
    )

    INVALID_AMOUNT_TOTAL = _("Not all invoice line items for invoice %(invoice)s have a amount total attached. "
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
        InvoicePaymentReceiveStatusValidator(invoice_payment)()

    @classmethod
    def validate_refund_payment(cls, user, invoice_payment):
        InvoicePaymentRefundStatusValidator(invoice_payment)()

    @classmethod
    def validate_cancel_payment(cls, user, invoice_payment):
        InvoicePaymentCancelStatusValidator(invoice_payment)()

    @classmethod
    def _validate_payment_match_items(cls, user, invoice_payment: InvoicePayment):
        line_items = [x.amount_total for x in invoice_payment.invoice.line_items.all()]
        if None in line_items:
            raise ValidationError(cls.INVALID_AMOUNT_TOTAL % {
                'invoice': invoice_payment.invoice
            })
        expected_amount = sum(line_items)
        if expected_amount != invoice_payment.amount_payed:
            raise ValidationError(cls.AMOUNT_PAYED_NOT_MATCHING_ITEMS % {
                'invoice': invoice_payment.invoice,
                'expected': expected_amount,
                'payed': invoice_payment.amount_payed
            })
