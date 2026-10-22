import datetime

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def __as_date(value):
    return value.date() if isinstance(value, datetime.datetime) else value


def validate_date_validity_range(**data):
    date_valid_from = data.get('date_valid_from')
    date_valid_to = data.get('date_valid_to')
    if date_valid_from and date_valid_to and __as_date(date_valid_to) < __as_date(date_valid_from):
        raise ValidationError(_("mutation.date_valid_to_before_date_valid_from"))


def validate_date_validity_range_on_create(model, **data):
    if data.get('date_valid_from') is None:
        default_date_valid_from = model._meta.get_field('date_valid_from').get_default()
        data = {**data, 'date_valid_from': default_date_valid_from}
    validate_date_validity_range(**data)


def validate_date_validity_range_on_update(model, **data):
    if data.get('date_valid_from') is None:
        stored_date_valid_from = model.objects.filter(id=data['id']).values_list(
            'date_valid_from', flat=True
        ).first()
        data = {**data, 'date_valid_from': stored_date_valid_from}
    validate_date_validity_range(**data)
