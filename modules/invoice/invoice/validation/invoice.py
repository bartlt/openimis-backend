from datetime import date
from enum import Enum
from typing import Union

from core.models import HistoryBusinessModel, HistoryModel, BaseVersionedModel
from invoice.models import Invoice
from invoice.validation import BaseInvoiceValidation


class InvoiceItemStatus(Enum):
    VALID = 0
    NO_ITEM = 1
    INVALID_ITEM = 2


class InvoiceModelValidation(BaseInvoiceValidation):
    OBJECT_TYPE = Invoice

    @classmethod
    def validate_subject(cls, invoice: Invoice):
        subject = invoice.subject
        item_status = cls._get_item_status(subject)
        return item_status

    @classmethod
    def validate_line_items(cls, invoice: Invoice):
        statuses = {}
        for item in invoice.line_items.all():
            status = cls._get_item_status(item.line)
            statuses[item] = status
        return statuses

    @classmethod
    def _get_item_status(cls, subject: Union[HistoryModel, BaseVersionedModel]):
        if subject is None:
            return InvoiceItemStatus.NO_ITEM
        else:
            if not cls.__valid_model(subject):
                return InvoiceItemStatus.INVALID_ITEM
        return InvoiceItemStatus.VALID

    @classmethod
    def __valid_model(cls, subject):
        # TODO: We should include generic method for checking if model is valid in both history model and
        # BaseVersionedModel
        if isinstance(subject, HistoryBusinessModel):
            return cls._validate_history_business_model(subject)
        elif isinstance(subject, HistoryModel):
            return cls._validate_history_model(subject)
        elif isinstance(subject, BaseVersionedModel):
            return cls._invoice_validate_base_versioned_model(subject)

    @classmethod
    def _validate_history_model(cls, subject: HistoryModel) -> bool:
        return not subject.is_deleted

    @classmethod
    def _validate_history_business_model(cls, subject: HistoryBusinessModel) -> bool:
        return cls._validate_history_model(subject) \
               and (subject.date_valid_to is None or subject.date_valid_to >= date.today())

    @classmethod
    def _invoice_validate_base_versioned_model(cls, subject: BaseVersionedModel) -> bool:
        return subject.validity_to is None
