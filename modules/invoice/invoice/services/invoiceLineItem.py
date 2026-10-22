from json import JSONDecodeError

import json

from invoice.models import InvoiceLineItem
from core.services import BaseService
from core.services.utils import get_generic_type
from invoice.validation.invoiceLineItem import InvoiceLineItemModelValidation

import logging

logger = logging.getLogger(__name__)


class InvoiceLineItemService(BaseService):

    OBJECT_TYPE = InvoiceLineItem

    def __init__(self, user, validation_class: InvoiceLineItemModelValidation = InvoiceLineItemModelValidation):
        super().__init__(user, validation_class)

    def _base_payload_adjust(self, invoice_data):
        adjusted_generics = self._evaluate_generic_types(invoice_data)
        adjusted_details = self._adjust_details_field(adjusted_generics)
        adjusted_calculations = self._calculate_payload_values(adjusted_details)
        return adjusted_calculations

    def _evaluate_generic_types(self, invoice_data):
        if 'line_type' in invoice_data.keys():
            invoice_data['line_type'] = get_generic_type(invoice_data['line_type'])
        return invoice_data

    def _calculate_payload_values(self, invoice_data):
        if 'amount_net' not in invoice_data.keys():
            invoice_data['amount_net'] = self.__calculate_net(invoice_data)
        if 'amount_total' not in invoice_data.keys():
            invoice_data['amount_total'] = self.__calculate_total(invoice_data)
        return invoice_data

    def _adjust_details_field(self, invoice_data):
        if invoice_data.get("details", None):
            details = invoice_data.get('details')
            if isinstance(details, dict):
                return invoice_data
            elif isinstance(details, str):
                try:
                    data = json.loads(details)
                except JSONDecodeError as e:
                    logger.exception("Failed to parse invoice line item "
                                     f"details {details}, conent will be saved in text"
                                     f"field")
                    data = {'text': details}
                invoice_data['details'] = data
            else:
                raise TypeError(f"Invalid type for InvoiceLineItem.details "
                                f"{type(details)}. Expected str or dict.")
        return invoice_data

    def __calculate_net(self, invoice_data):
        quantity = invoice_data.get('quantity', 0)
        unit_price = invoice_data.get('unit_price', 0)
        discount = invoice_data.get('discount', 0)
        return (quantity * unit_price) - discount

    def __calculate_total(self, invoice_data):
        tax_total = self.__get_tax_total(invoice_data)
        return invoice_data.get('amount_net', 0) + tax_total

    def __get_tax_total(self, invoice_data):
        tax_data = invoice_data.get('tax_analysis', {'total': 0})
        if isinstance(tax_data, str):
            tax_data = json.loads(tax_data)
        if 'total' not in tax_data.keys():
            logger.warning("Invalid 'tax_analysis' format, total field not found")
            return 0
        else:
            return float(tax_data['total'])
