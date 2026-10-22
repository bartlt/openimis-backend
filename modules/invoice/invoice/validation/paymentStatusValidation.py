from abc import ABC
from typing import Union, Iterable

from django.core.exceptions import ValidationError

from invoice.models import InvoicePayment, Invoice
from django.utils.translation import gettext as _


class GenericPaymentStatusValidation(ABC):
    @property
    def allowed_invoice_statuses(self) -> Iterable[Invoice.Status]:
        """
        Iterable of valid invoice statuses.
        """
        raise NotImplementedError()

    @property
    def allowed_payment_statuses(self):
        """
        Iterable of valid invoice payment statuses.
        """
        raise NotImplementedError()

    @property
    def error_message_invalid_invoice(self):
        """
        gettext string for content of ValidationError message raised when invoice status is invalid.
        """
        raise NotImplementedError()

    @property
    def error_message_invalid_payment(self):
        """
        gettext string for content of ValidationError message raised when invoice payment status is invalid.
        """
        raise NotImplementedError()

    @property
    def error_message_vars(self):
        """
        Returns dictionary of variables used by error messages.
        """
        invoice_status = self.invoice_payment.invoice.status
        payment_status = self.invoice_payment.status
        return {
            'invoice': self.invoice_payment.invoice,
            'payment': self.invoice_payment,
            'invoice_status':
                invoice_status.label if isinstance(invoice_status, Invoice.Status) else invoice_status,
            'payment_status':
                payment_status.label if isinstance(payment_status, InvoicePayment.PaymentStatus)
                else payment_status,
            'allowed_invoice': ', '.join([x.label for x in self.allowed_invoice_statuses]),
            'allowed_payment': ', '.join([x.label for x in self.allowed_payment_statuses]),
        }

    def __init__(self, invoice_payment):
        self.invoice_payment = invoice_payment

    def __call__(self, *args, **kwargs):
        self.validate()

    def validate(self):
        self._validate_invoice()
        self._validate_payment()

    @classmethod
    def _validate_status(
            cls, status: Union[InvoicePayment.PaymentStatus, Invoice.Status],
            allowed: Union[Iterable[InvoicePayment.PaymentStatus], Iterable[Invoice.Status]],
            err_msg):
        if status not in allowed:
            raise ValidationError(err_msg)

    def _validate_invoice(self):
        status = self.invoice_payment.invoice.status
        allowed = self.allowed_invoice_statuses
        err_msg = self.error_message_invalid_invoice % self.error_message_vars
        return self._validate_status(status, allowed, err_msg)

    def _validate_payment(self):
        status = self.invoice_payment.status
        allowed = self.allowed_payment_statuses
        err_msg = self.error_message_invalid_payment % self.error_message_vars
        return self._validate_status(status, allowed, err_msg)


class InvoicePaymentReceiveStatusValidator(GenericPaymentStatusValidation):
    allowed_invoice_statuses = [Invoice.Status.DRAFT, Invoice.Status.VALIDATED]

    error_message_invalid_invoice = _(
        "Payment for invoice %(invoice)s can't be made. Invoice has to be in status"
        "[%(allowed_invoice)s]. Invoice status is %(invoice_status)s."
    )

    allowed_payment_statuses = \
        [InvoicePayment.PaymentStatus.ACCEPTED, InvoicePayment.PaymentStatus.REJECTED]

    error_message_invalid_payment = _(
        "It's not possible to set payment status to %(payment_status)s during payment. Allowed statuses are "
        "%(allowed_payment)s."
    )


class InvoicePaymentRefundStatusValidator(GenericPaymentStatusValidation):
    allowed_invoice_statuses = [Invoice.Status.PAID]
    error_message_invalid_invoice = _(
        "Invoice %(invoice)s can't be refunded. Invoice has to be in PAYED status, currently it's %(invoice_status)s."
    )

    allowed_payment_statuses = [InvoicePayment.PaymentStatus.ACCEPTED]
    error_message_invalid_payment = _(
        "It's not possible to refund payment %(payment)s, as it's in %(payment_status) status. "
        "Only ACCEPTED payments can be refunded."
    )


class InvoicePaymentCancelStatusValidator(GenericPaymentStatusValidation):
    allowed_invoice_statuses = [Invoice.Status.PAID]

    error_message_invalid_invoice = _(
        "Invoice %(invoice)s can't be canceled. Invoice has to be in PAYED status, currently it's %(invoice_status)s."
    )

    allowed_payment_statuses = [InvoicePayment.PaymentStatus.ACCEPTED]
    error_message_invalid_payment = _(
        "It's not possible to cancel payment %(payment)s, only ACCEPTED payments can be canceled."
    )
