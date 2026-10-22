import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from contribution_plan.gql.gql_mutations.validation import (
    validate_date_validity_range,
    validate_date_validity_range_on_create,
    validate_date_validity_range_on_update,
)
from contribution_plan.models import ContributionPlanBundle
from contribution_plan.tests.helpers import create_test_contribution_plan_bundle


class ValidationTestDateValidityRange(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ValidationTestDateValidityRange, cls).setUpClass()
        cls.test_contribution_plan_bundle = create_test_contribution_plan_bundle(
            custom_props={
                'code': "Validation range " + str(datetime.datetime.now()),
                'date_valid_from': datetime.datetime(2025, 6, 1),
            }
        )

    def test_date_valid_to_after_date_valid_from(self):
        validate_date_validity_range(
            date_valid_from=datetime.date(2025, 5, 1),
            date_valid_to=datetime.date(2025, 6, 1),
        )

    def test_date_valid_to_before_date_valid_from(self):
        with self.assertRaises(ValidationError) as context:
            validate_date_validity_range(
                date_valid_from=datetime.date(2025, 6, 1),
                date_valid_to=datetime.date(2025, 5, 1),
            )
        self.assertIn("date_valid_to_before_date_valid_from", str(context.exception))

    def test_equal_dates_are_accepted(self):
        validate_date_validity_range(
            date_valid_from=datetime.date(2025, 6, 1),
            date_valid_to=datetime.date(2025, 6, 1),
        )

    def test_date_from_model_and_date_from_input_are_comparable(self):
        with self.assertRaises(ValidationError):
            validate_date_validity_range(
                date_valid_from=datetime.datetime(2025, 6, 1, 14, 30),
                date_valid_to=datetime.date(2025, 5, 1),
            )

    def test_without_date_valid_to_nothing_is_validated(self):
        validate_date_validity_range(date_valid_from=datetime.date(2025, 6, 1))

    def test_create_without_date_valid_from_uses_model_default(self):
        with self.assertRaises(ValidationError) as context:
            validate_date_validity_range_on_create(
                ContributionPlanBundle, date_valid_to=datetime.date(2020, 1, 1)
            )
        self.assertIn("date_valid_to_before_date_valid_from", str(context.exception))

    def test_create_without_date_valid_from_accepts_future_date_valid_to(self):
        validate_date_validity_range_on_create(
            ContributionPlanBundle,
            date_valid_to=datetime.date.today() + datetime.timedelta(days=1),
        )

    def test_update_without_date_valid_from_uses_stored_value(self):
        with self.assertRaises(ValidationError) as context:
            validate_date_validity_range_on_update(
                ContributionPlanBundle,
                id=self.test_contribution_plan_bundle.id,
                date_valid_to=datetime.date(2025, 5, 1),
            )
        self.assertIn("date_valid_to_before_date_valid_from", str(context.exception))

    def test_update_with_explicit_none_date_valid_from_uses_stored_value(self):
        with self.assertRaises(ValidationError):
            validate_date_validity_range_on_update(
                ContributionPlanBundle,
                id=self.test_contribution_plan_bundle.id,
                date_valid_from=None,
                date_valid_to=datetime.date(2025, 5, 1),
            )

    def test_update_with_date_valid_from_in_payload_ignores_stored_value(self):
        validate_date_validity_range_on_update(
            ContributionPlanBundle,
            id=self.test_contribution_plan_bundle.id,
            date_valid_from=datetime.date(2025, 1, 1),
            date_valid_to=datetime.date(2025, 5, 1),
        )
