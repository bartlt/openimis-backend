from json import JSONDecodeError

import json

from invoice.models import BillItem
from core.services import BaseService
from core.services.utils import get_generic_type
from invoice.validation.billLineItem import BillLineItemModelValidation

import logging

logger = logging.getLogger(__name__)


class BillLineItemService(BaseService):

    OBJECT_TYPE = BillItem

    def __init__(self, user, validation_class: BillLineItemModelValidation = BillLineItemModelValidation):
        super().__init__(user, validation_class)

    def _base_payload_adjust(self, bill_data):
        adjusted_generics = self._evaluate_generic_types(bill_data)
        adjusted_details = self._adjust_details_field(adjusted_generics)
        adjusted_calculations = self._calculate_payload_values(adjusted_details)
        return adjusted_calculations

    def _evaluate_generic_types(self, bill_data):
        if 'line_type' in bill_data.keys():
            bill_data['line_type'] = get_generic_type(bill_data['line_type'])
        return bill_data

    def _calculate_payload_values(self, bill_data):
        if 'amount_net' not in bill_data.keys():
            bill_data['amount_net'] = self.__calculate_net(bill_data)
        if 'amount_total' not in bill_data.keys():
            bill_data['amount_total'] = self.__calculate_total(bill_data)
        return bill_data

    def _adjust_details_field(self, bill_data):
        if bill_data.get("details", None):
            details = bill_data.get('details')
            if isinstance(details, dict):
                return bill_data
            elif isinstance(details, str):
                try:
                    data = json.loads(details)
                except JSONDecodeError as e:
                    logger.exception("Failed to parse bill line item "
                                     f"details {details}, conent will be saved in text"
                                     f"field")
                    data = {'text': details}
                bill_data['details'] = data
            else:
                raise TypeError(f"Invalid type for BillItem.details "
                                f"{type(details)}. Expected str or dict.")
        return bill_data

    def __calculate_net(self, bill_data):
        quantity = bill_data.get('quantity', 0)
        unit_price = bill_data.get('unit_price', 0)
        discount = bill_data.get('discount', 0)
        return (quantity * unit_price) - discount

    def __calculate_total(self, bill_data):
        tax_total = self.__get_tax_total(bill_data)
        return bill_data.get('amount_net', 0) + tax_total

    def __get_tax_total(self, bill_data):
        tax_data = bill_data.get('tax_analysis', {'total': 0})
        if isinstance(tax_data, str):
            tax_data = json.loads(tax_data)
        if 'total' not in tax_data.keys():
            logger.warning("Invalid 'tax_analysis' format, total field not found")
            return 0
        else:
            return float(tax_data['total'])
