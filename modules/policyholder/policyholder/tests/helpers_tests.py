from functools import lru_cache

from django.test import TestCase

from policyholder.models import PolicyHolder, PolicyHolderInsuree, PolicyHolderUser
from policyholder.tests import create_test_policy_holder, create_test_policy_holder_insuree, \
    create_test_policy_holder_user


class HelpersTest(TestCase):
    """
    Class to check whether the helper methods responsible for creating test data work correctly.
    """

    @classmethod
    def setUpClass(cls):
        super(HelpersTest, cls).setUpClass()
        cls.policy_holder = cls.__create_test_policy_holder()
        cls.policy_holder_custom = cls.__create_test_policy_holder(custom=True)

        cls.policy_holder_insuree = cls.__create_test_policy_holder_insuree()
        cls.policy_holder_insuree_custom = cls.__create_test_policy_holder_insuree(custom=True)

        cls.policy_holder_user = cls.__create_test_policy_holder_user()
        cls.policy_holder_user_custom = cls.__create_test_policy_holder_user(custom=True)

    def test_create_policy_holder(self):
        db_policy_holder = PolicyHolder.objects.filter(id=self.policy_holder.id).first()
        self.assertEqual(db_policy_holder, self.policy_holder, "Failed to create policy holder in helper")

    def test_create_policy_holder_insuree(self):
        db_policy_holder_insuree = PolicyHolderInsuree.objects.filter(id=self.policy_holder_insuree.id).first()

        self.assertEqual(db_policy_holder_insuree, self.policy_holder_insuree,
                         "Failed to create policy holder insuree in helper")

    def test_create_policy_holder_user(self):
        db_policy_holder_user = PolicyHolderUser.objects.filter(id=self.policy_holder_user.id).first()

        self.assertEqual(db_policy_holder_user, self.policy_holder_user,
                         "Failed to create policy holder insuree in helper")

    def test_create_policy_holder_custom_params(self):
        db_policy_holder = PolicyHolder.objects.filter(id=self.policy_holder_custom.id).first()
        params = self.__custom_policy_holder_params()
        self.assertEqual(db_policy_holder.code, params['code'])
        self.assertEqual(db_policy_holder.trade_name, params['trade_name'])
        self.assertEqual(db_policy_holder.activity_code, params['activity_code'])

    def test_create_policy_holder_insuree_custom_params(self):
        db_policy_holder_insuree = PolicyHolderInsuree.objects.filter(id=self.policy_holder_insuree_custom.id).first()
        params = self.__custom_policy_holder_insuree_params()
        self.assertEqual(db_policy_holder_insuree.policy_holder, params['policy_holder'])
        self.assertEqual(db_policy_holder_insuree.version, 1)

    def test_create_policy_holder_user_custom_params(self):
        db_policy_holder_user = PolicyHolderUser.objects.filter(id=self.policy_holder_user_custom.id).first()
        params = self.__custom_policy_holder_user_params()
        self.assertEqual(db_policy_holder_user.policy_holder, params['policy_holder'])
        self.assertEqual(db_policy_holder_user.is_deleted, True)

    @classmethod
    @lru_cache(maxsize=2)
    def __custom_policy_holder_params(cls):
        return {
            'code': 'CustomCode',
            'trade_name': 'CustomTradeName',
            'activity_code': -1,
        }

    @classmethod
    @lru_cache(maxsize=2)
    def __custom_policy_holder_insuree_params(cls):
        return {
            'policy_holder': cls.__create_test_policy_holder(custom=True),
        }

    @classmethod
    @lru_cache(maxsize=2)
    def __custom_policy_holder_user_params(cls):
        return {
            'policy_holder': cls.__create_test_policy_holder(custom=True),
            'is_deleted': True
        }

    @classmethod
    def __create_test_instance(cls, function, **kwargs):
        if kwargs:
            return function(**kwargs)
        else:
            return function()

    @classmethod
    def __create_test_policy_holder(cls, custom=False):
        custom_params = cls.__custom_policy_holder_params() if custom else {}
        return cls.__create_test_instance(create_test_policy_holder, custom_props=custom_params)

    @classmethod
    def __create_test_policy_holder_insuree(cls, custom=False):
        custom_params = cls.__custom_policy_holder_insuree_params() if custom else {}
        return cls.__create_test_instance(create_test_policy_holder_insuree, custom_props=custom_params)

    @classmethod
    def __create_test_policy_holder_user(cls, custom=False):
        custom_params = cls.__custom_policy_holder_user_params() if custom else {}
        return cls.__create_test_instance(create_test_policy_holder_user, custom_props=custom_params)
