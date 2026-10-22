from typing import Union, List

from invoice.models import Invoice, InvoiceLineItem
from core.services import BaseService
from core.services.utils import get_generic_type
from invoice.services.invoiceLineItem import InvoiceLineItemService
from invoice.validation.invoice import InvoiceModelValidation, InvoiceItemStatus
from core.signals import *


class InvoiceService(BaseService):
    OBJECT_TYPE = Invoice

    def __init__(self, user, validation_class: InvoiceModelValidation = InvoiceModelValidation):
        super().__init__(user, validation_class)
        self.validation_class = validation_class

    def _base_payload_adjust(self, invoice_data):
        return self._evaluate_generic_types(invoice_data)

    def invoice_validate_items(self, invoice: Invoice):
        # TODO: Implement after calculation rules available
        pass

    def invoice_match_items(self, invoice: Invoice) \
            -> Dict[str, Union[InvoiceItemStatus, Dict[InvoiceLineItem, List[InvoiceItemStatus]]]]:
        """
        Check if items related to invoice are valid.
        @param invoice: Invoice object
        @return: Dict with two keys, 'subject_status' containing information if invoice subject is valid and
        'line_items', containing information about statuses of lines connected to invoice items.
        """
        match_result = {
            'subject': self.validation_class.validate_subject(invoice),
            'line_items': self.validation_class.validate_line_items(invoice)
        }
        return match_result

    def invoiceTaxCalculation(self, invoice: Invoice):
        # TODO: Implement after calculation rules available
        pass

    @classmethod
    @register_service_signal('invoice_creation_from_calculation')
    def invoice_creation_from_calculation(cls, user, from_date, to_date):
        """
        It sends the invoice_creation_from_calculation signal which should inform the
        relevant calculation rule that invoices need to be generated.
        """
        pass

    def _evaluate_generic_types(self, invoice_data):
        if 'subject_type' in invoice_data.keys():
            invoice_data['subject_type'] = get_generic_type(invoice_data['subject_type'])

        if 'thirdparty_type' in invoice_data.keys():
            invoice_data['thirdparty_type'] = get_generic_type(invoice_data['thirdparty_type'])

        return invoice_data

    @classmethod
    @register_service_signal('signal_after_invoice_module_invoice_create_service')
    def invoice_create(cls, **kwargs):
        convert_results = kwargs.get('result', {})
        if 'invoice_data' in convert_results and 'invoice_data_line' in convert_results:
            user = convert_results['user']
            # save in database this invoice and invoice line item
            invoice_line_items = convert_results['invoice_data_line']
            invoice_service = InvoiceService(user=user)
            invoice_line_item_service = InvoiceLineItemService(user=user)
            result_invoice = invoice_service.create(convert_results['invoice_data'])
            if result_invoice["success"] is True:
                invoice_update = {
                    "id": result_invoice["data"]["id"],
                    "amount_net": 0,
                    "amount_total": 0,
                    "amount_discount": 0
                }
                for invoice_line_item in invoice_line_items:
                    invoice_line_item["invoice_id"] = result_invoice["data"]["id"]
                    result_invoice_line = invoice_line_item_service.create(invoice_line_item)
                    if result_invoice_line["success"] is True:
                        invoice_update["amount_net"] += float(result_invoice_line["data"]["amount_net"])
                        invoice_update["amount_total"] += float(result_invoice_line["data"]["amount_total"])
                        invoice_update["amount_discount"] += 0 if result_invoice_line["data"]["discount"] else \
                            result_invoice_line["data"]["discount"]
                generated_invoice = invoice_service.update(invoice_update)
                return generated_invoice
