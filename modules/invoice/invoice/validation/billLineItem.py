from invoice.models import BillItem
from core.validation import BaseModelValidation


class BillLineItemModelValidation(BaseModelValidation):
    OBJECT_TYPE = BillItem
