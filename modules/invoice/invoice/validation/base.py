from abc import ABC

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from core.validation import BaseModelValidation, UniqueCodeValidationMixin, ObjectExistsValidationMixin


class TaxAnalysisFormatValidationMixin:
    INVALID_TAX_ANALYSIS_JSON_FORMAT_NO_KEYS = _("Invalid tax_analysis format, 'total' and 'lines' keys are required.")

    INVALID_TAX_ANALYSIS_JSON_FORMAT_LINES_KEYS = _("tax_analysis.lines is not in list format.")

    INVALID_TAX_ANALYSIS_JSON_FORMAT_LINES_FORMAT = _("tax_analysis.lines content is not a dict.")

    @classmethod
    def validate_tax_analysis_format(cls, tax: dict):
        if tax and not cls._has_required_keys(tax):
            raise ValidationError(cls.INVALID_TAX_ANALYSIS_JSON_FORMAT_NO_KEYS)

        # TODO when tax calculation rule is available then remove this condition
        if tax:
            lines = tax['lines']
            if not isinstance(lines, list):
                raise ValidationError(cls.INVALID_TAX_ANALYSIS_JSON_FORMAT_LINES_KEYS)

            for line in lines:
                if not isinstance(line, dict):
                    raise ValidationError(cls.INVALID_TAX_ANALYSIS_JSON_FORMAT_LINES_FORMAT)

    @classmethod
    def _has_required_keys(cls, tax: dict):
        keys = tax.keys()
        if 'total' not in keys or 'lines' not in keys:
            return False
        return True


class BaseInvoiceValidation(BaseModelValidation, UniqueCodeValidationMixin,
                            TaxAnalysisFormatValidationMixin, ObjectExistsValidationMixin, ABC):

    @classmethod
    def validate_create(cls, user, **data):
        cls.validate_unique_code_name(data.get('code', None))
        cls.validate_tax_analysis_format(data.get('tax_analysis', None))

    @classmethod
    def validate_update(cls, user, **data):
        cls.validate_object_exists(data.get('id', None))
        code = data.get('code', None)
        id_ = data.get('id', None)

        if code:
            cls.validate_unique_code_name(code, id_)

        cls.validate_tax_analysis_format(data.get('tax_analysis', None))
