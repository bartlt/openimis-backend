from django.db import transaction

from core.services import BaseService
from core.services.utils import (
    check_authentication,
    output_exception,
    output_result_success,
    model_representation
)
from core.signals import *
from invoice.models import (
    Bill,
    PaymentInvoice,
    Invoice,
    DetailPaymentInvoice
)
from invoice.utils import resolve_payment_details
from invoice.validation.paymentInvoice import PaymentInvoiceModelValidation


class PaymentInvoiceService(BaseService):

    OBJECT_TYPE = PaymentInvoice

    def __init__(self, user, validation_class: PaymentInvoiceModelValidation = PaymentInvoiceModelValidation):
        super().__init__(user, validation_class)
        self.validation_class = validation_class

    @check_authentication
    def update(self, obj_data):
        raise NotImplementedError("Update method is not implemented for PaymentInvoice")

    @check_authentication
    def create_with_detail(self, payment_invoice: dict, payment_detail: DetailPaymentInvoice):
        try:
            with transaction.atomic():
                payment = PaymentInvoice(**payment_invoice)
                payment.save(user=self.user)
                payment_detail.payment = payment
                payment_detail.subject = self._get_generic_object(
                    payment_detail.subject_id,
                    payment_detail.subject_type
                )
                if 'reconciliation' in payment.json_ext:
                    payment_detail.reconcilation_id = payment.json_ext['reconciliation']['id']
                payment_detail.save(user=self.user)
                dict_repr = model_representation(payment)
                dict_repr['payment_detail_uuid'] = payment_detail.uuid
                return output_result_success(dict_representation=dict_repr)
        except Exception as exc:
            return output_exception(model_name="PaymentInvoice", method="create_with_detail", exception=exc)

    @check_authentication
    @register_service_signal('signal_after_invoice_module_ref_received')
    def ref_received(self, payment_invoice: PaymentInvoice, payment_ref):
        try:
            with transaction.atomic():
                self.validation_class.validate_ref_received(self.user, payment_invoice, payment_ref)
                payment_invoice.code_ext = payment_ref
                return self.save_instance(payment_invoice)
        except Exception as exc:
            return output_exception(model_name="PaymentInvoice", method="ref_received", exception=exc)

    @register_service_signal('signal_after_invoice_module_payment_received')
    def payment_received(self, payment_invoice: PaymentInvoice, payment_status: DetailPaymentInvoice.DetailPaymentStatus):
        try:
            with transaction.atomic():
                self.validation_class.validate_receive_payment(self.user, payment_invoice)
                self._update_all_dependencies_for_payment(
                    payment_invoice,
                    payment_status,
                    Invoice.Status.PAID
                )
                dict_repr = model_representation(payment_invoice)
                return output_result_success(dict_representation=dict_repr)
        except Exception as exc:
            return output_exception(model_name="PaymentInvoice", method="payment_received", exception=exc)

    @register_service_signal('signal_after_invoice_module_payment_refunded')
    def payment_refunded(self, payment_invoice):
        try:
            with transaction.atomic():
                self._update_all_dependencies_for_payment(
                    payment_invoice,
                    DetailPaymentInvoice.DetailPaymentStatus.REFUNDED,
                    Invoice.Status.SUSPENDED
                )
                dict_repr = model_representation(payment_invoice)
                return output_result_success(dict_representation=dict_repr)
        except Exception as exc:
            return output_exception(model_name="PaymentInvoice", method="payment_refunded", exception=exc)

    @register_service_signal('signal_after_invoice_module_payment_cancelled')
    def payment_cancelled(self, payment_invoice):
        try:
            with transaction.atomic():
                self._update_all_dependencies_for_payment(
                    payment_invoice,
                    DetailPaymentInvoice.DetailPaymentStatus.CANCELLED,
                    Invoice.Status.SUSPENDED
                )
                dict_repr = model_representation(payment_invoice)
                return output_result_success(dict_representation=dict_repr)
        except Exception as exc:
            return output_exception(model_name="PaymentInvoice", method="payment_cancelled", exception=exc)

    def _update_all_dependencies_for_payment(self, payment_invoice, payment_status, invoice_status):
        invoices, bills = resolve_payment_details(payment_invoice)
        payment_details = payment_invoice.invoice_payments.all()
        self._update_detail(payment_details, payment_status)
        self._update_detail(invoices, invoice_status)
        self._update_detail(bills, invoice_status)

    def _update_detail(self, detail_collection, status):
        for detail in detail_collection:
            if detail.status != status:
                detail.status = status
                detail.save(user=self.user)

    @classmethod
    def _get_generic_object(cls, subject_id, subject_type):
        if subject_type.model == 'invoice':
            object = Invoice.objects.get(id=subject_id)
        else:
            object = Bill.objects.get(id=subject_id)
        return object
