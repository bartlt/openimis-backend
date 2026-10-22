from django.core.exceptions import ValidationError

from policyholder.models import PolicyHolder


class PolicyHolderValidation:
    UNIQUE_DISPLAY_NAME_VALIDATION_ERROR = "Display name '{} {}' already in use"
    UNMUTABLE_FIELD_UPDATE_ATTEMPT = "Field '{}' cannot be updated"

    @classmethod
    def validate_create(cls, user, **data):
        code = data.get('code', None)
        trade_name = data.get('trade_name', None)
        if not cls.__unique_display_name(code, trade_name):
            raise ValidationError(cls.UNIQUE_DISPLAY_NAME_VALIDATION_ERROR.format(code, trade_name))

    @classmethod
    def validate_update(cls, user, **data):
        existing = PolicyHolder.objects.filter(id=data['id']).first()
        code = data.get('code', existing.code)  # New or current
        trade_name = data.get('trade_name', existing.trade_name)  # New or current
        duplicated = PolicyHolder.objects.filter(code=code, trade_name=trade_name).exclude(id=data['id']).exists()

        if duplicated:
            raise ValidationError(cls.UNIQUE_DISPLAY_NAME_VALIDATION_ERROR.format(code, trade_name))

        if unmutable_attempt := cls.__validate_unmutable_update_attempt(existing, data):
            raise ValidationError(
                "\n".join(unmutable_attempt)
            )

    @classmethod
    def __validate_unmutable_update_attempt(cls, existing: PolicyHolder, updated: dict):
        # Code and date Valid from cannot be changed, see step 1 from `Edit assigned policy holder insuree`` Test Case
        validation_results = []
        if existing.code != updated.get('code', existing.code):
            validation_results.append(cls.UNMUTABLE_FIELD_UPDATE_ATTEMPT.format('code'))
        if existing.date_valid_from.date() != updated.get('date_valid_from', existing.date_valid_from.date()):
            validation_results.append(cls.UNMUTABLE_FIELD_UPDATE_ATTEMPT.format('date_valid_from'))

        return validation_results

    @classmethod
    def __unique_display_name(cls, code, trade_name):
        return not PolicyHolder.objects.filter(code=code, trade_name=trade_name).exists()
