from functools import lru_cache
from django.test import TestCase

from contribution_plan.models import ContributionPlanBundle, ContributionPlan, ContributionPlanBundleDetails
from contribution_plan.tests.helpers import create_test_contribution_plan_bundle, create_test_contribution_plan, \
    create_test_contribution_plan_bundle_details


class HelpersTest(TestCase):
    """
    Class to check whether the helper methods responsible for creating test data work correctly.
    """

    @classmethod
    def setUpClass(cls):
        super(HelpersTest, cls).setUpClass()
        cls.contribution_plan_bundle = cls.__create_test_contribution_plan_bundle()
        cls.contribution_plan_bundle_custom = cls.__create_test_contribution_plan_bundle(custom=True)

        cls.contribution_plan = cls.__create_test_contribution_plan()
        cls.contribution_plan_custom = cls.__create_test_contribution_plan(custom=True)

        cls.contribution_plan_details = cls.__create_test_contribution_plan_details()
        cls.contribution_plan_details_custom = cls.__create_test_contribution_plan_details(custom=True)

    def test_create_test_contribution_plan_bundle(self):
        db_contribution_plan_bundle = ContributionPlanBundle.objects \
            .filter(id=self.contribution_plan_bundle.uuid).first()

        self.assertEqual(db_contribution_plan_bundle, self.contribution_plan_bundle,
                         "Failed to create contribution plan bundle in helper")

    def test_base_create_contribution_plan_bundle_custom_params(self):
        db_contribution_plan_bundle = ContributionPlanBundle.objects \
            .filter(id=self.contribution_plan_bundle_custom.uuid).first()

        params = self.__get_custom_contribution_plan_bundle_params()
        self.assertEqual(db_contribution_plan_bundle.version, 1)
        self.assertEqual(db_contribution_plan_bundle.name, params['name'])

    def test_create_test_contribution_plan(self):
        db_contribution_plan = ContributionPlan.objects.filter(id=self.contribution_plan.uuid).first()

        self.assertEqual(db_contribution_plan, self.contribution_plan, "Failed to create contribution plan in helper")

    def test_create_contribution_plan_custom_params(self):
        db_contribution_plan = ContributionPlan.objects.filter(id=self.contribution_plan_custom.uuid).first()

        params = self.__get_custom_contribution_plan_params()
        self.assertEqual(db_contribution_plan.is_deleted, params['is_deleted'])
        self.assertEqual(db_contribution_plan.code, params['code'])
        self.assertEqual(db_contribution_plan.periodicity, params['periodicity'])

    def test_create_test_contribution_plan_details(self):
        db_contribution_plan_details = ContributionPlanBundleDetails.objects \
            .filter(id=self.contribution_plan_details.uuid).first()

        self.assertEqual(db_contribution_plan_details, self.contribution_plan_details,
                         "Failed to create contribution plan details in helper")

    def test_base_create_contribution_plan_details_custom_params(self):
        db_contribution_plan_details = ContributionPlanBundleDetails.objects \
            .filter(id=self.contribution_plan_details_custom.uuid).first()

        params = self.__get_custom_contribution_plan_details_params()
        self.assertEqual(db_contribution_plan_details.version, 1)
        self.assertEqual(db_contribution_plan_details.contribution_plan, params['contribution_plan'])
        self.assertEqual(db_contribution_plan_details.contribution_plan_bundle, params['contribution_plan_bundle'])

    @classmethod
    @lru_cache(maxsize=1)
    def __get_custom_contribution_plan_bundle_params(cls):
        return {
            'name': 'Updated CPB',
        }

    @classmethod
    @lru_cache(maxsize=1)
    def __get_custom_contribution_plan_params(cls):
        return {
            'is_deleted': True,
            'code': 'Updated code',
            'periodicity': 4,
        }

    @classmethod
    @lru_cache(maxsize=1)
    def __get_custom_contribution_plan_details_params(cls):
        return {
            'contribution_plan': cls.__create_test_contribution_plan(True),
            'contribution_plan_bundle': cls.__create_test_contribution_plan_bundle(True),
        }

    @classmethod
    def __create_test_instance(cls, function, **kwargs):
        if kwargs:
            return function(**kwargs)
        else:
            return function()

    @classmethod
    def __create_test_contribution_plan_bundle(cls, custom=False):
        custom_params = cls.__get_custom_contribution_plan_bundle_params() if custom else {}
        return cls.__create_test_instance(create_test_contribution_plan_bundle, custom_props=custom_params)

    @classmethod
    def __create_test_contribution_plan(cls, custom=False):
        custom_params = cls.__get_custom_contribution_plan_params() if custom else {}
        return cls.__create_test_instance(create_test_contribution_plan, custom_props=custom_params)

    @classmethod
    def __create_test_contribution_plan_details(cls, custom=False):
        custom_params = cls.__get_custom_contribution_plan_details_params() if custom else {}
        return cls.__create_test_instance(create_test_contribution_plan_bundle_details, custom_props=custom_params)
