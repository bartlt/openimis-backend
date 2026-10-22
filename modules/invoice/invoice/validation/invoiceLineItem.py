from invoice.models import InvoiceLineItem
from core.validation import BaseModelValidation


class InvoiceLineItemModelValidation(BaseModelValidation):
    OBJECT_TYPE = InvoiceLineItem
