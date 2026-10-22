from django.test import TestCase

from policyholder.services import PolicyHolder as PolicyHolderService, \
    PolicyHolderInsuree as PolicyHolderInsureeService, \
    PolicyHolderContributionPlan as PolicyHolderContributionPlanService
from policyholder.models import PolicyHolder, PolicyHolderInsuree, PolicyHolderContributionPlan
from policyholder.tests.helpers import create_test_policy_holder, create_test_policy_holder_insuree

from contribution_plan.tests.helpers_tests import create_test_contribution_plan_bundle
from insuree.test_helpers import create_test_insuree
from core.models import User

from policyholder.validation import PolicyHolderValidation


class ServiceTestPolicyHolder(TestCase):
    POLICY_HOLDER = {
        'code': 'TT_Code',
        'trade_name': 'COTO',
        'address': {"region": "APAC", "street": "test"},
        'phone': '111000111',
        'fax': 'Fax',
        'email': 'policy_holder@mail.com',
        'contact_name': {"name": "test", "surname": "test-test"},
        'legal_form': 1,
        'activity_code': 2,
        'accountancy_account': '128903719082739810273',
        'bank_account': {"IBAN": "PL00 0000 2345 0000 1000 2345 2345"},
        'payment_reference': 'PolicyHolderPaymentReference',
    }

    @classmethod
    def setUpClass(cls):
        super(ServiceTestPolicyHolder, cls).setUpClass()
        if not User.objects.filter(username='Admin').exists():
            User.objects.create_superuser(username='Admin', password='Spe®Pąßw0rd™')
        cls.user = User.objects.filter(username='Admin').first()
        cls.policy_holder_service = PolicyHolderService(cls.user)
        cls.policy_holder_insuree_service = PolicyHolderInsureeService(cls.user)
        cls.policy_holder_contribution_plan_service = PolicyHolderContributionPlanService(cls.user)

        cls.test_policy_holder = create_test_policy_holder(custom_props=cls.POLICY_HOLDER)
        cls.test_policy_holder_mini = create_test_policy_holder()
        cls.test_insuree = create_test_insuree()
        cls.test_policy_holder_insuree = create_test_policy_holder_insuree(policy_holder=cls.test_policy_holder, insuree=cls.test_insuree)
        cls.test_policy_holder_insuree = create_test_policy_holder_insuree(policy_holder=cls.test_policy_holder_mini, insuree=cls.test_insuree)

        cls.test_insuree_to_change = create_test_insuree()
        cls.test_contribution_plan_bundle = cls.test_policy_holder_insuree.contribution_plan_bundle
        cls.test_last_policy = cls.test_policy_holder_insuree.last_policy
        cls.test_contribution_plan_bundle_to_replace = create_test_contribution_plan_bundle()

    def test_policy_holder_create(self):
        self.POLICY_HOLDER['code'] = 'test_policy_holder_create'

        response = self.policy_holder_service.create(self.POLICY_HOLDER)

        # tear down the test data

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                self.POLICY_HOLDER['code'],
                self.POLICY_HOLDER['trade_name'],
                1,
                self.POLICY_HOLDER['bank_account'],
                self.POLICY_HOLDER['accountancy_account'],
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['code'],
                response['data']['trade_name'],
                response['data']['version'],
                response['data']['bank_account'],
                response['data']['accountancy_account'],
            )
        )

    def test_duplicate_policy_holder_exception(self):

        self.POLICY_HOLDER['code'] = 'qwerqwre'
        first = self.policy_holder_service.create(self.POLICY_HOLDER)
        second = self.policy_holder_service.create(self.POLICY_HOLDER)

        expected_error_message = PolicyHolderValidation.UNIQUE_DISPLAY_NAME_VALIDATION_ERROR \
            .format(self.POLICY_HOLDER['code'], self.POLICY_HOLDER['trade_name'])
        self.assertTrue(first['success'])
        self.assertFalse(second['success'])
        self.assertTrue(expected_error_message in second['detail'])

    def test_policy_holder_create_update(self):
        self.POLICY_HOLDER['code'] = 'ddsdfsdffff'
        response = self.policy_holder_service.create(self.POLICY_HOLDER)
        policy_holder_object = PolicyHolder.objects.get(id=response['data']['id'])
        # version = policy_holder_object.version
        policy_holder = {
            'id': str(policy_holder_object.id),
            'address': {"region": "TEST", "street": "TEST"},
        }
        response = self.policy_holder_service.update(policy_holder)

        # tear down the test data
        PolicyHolder.objects.filter(code=self.POLICY_HOLDER['code']).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                {"region": "TEST", "street": "TEST"},
                2,
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['address'],
                response['data']['version'],
            )
        )

    def test_policy_holder_update_without_changing_field(self):
        self.POLICY_HOLDER['code'] = 'ddsseedfth'
        ph = self.policy_holder_service.create(self.POLICY_HOLDER)
        policy_holder_object = PolicyHolder.objects.filter(id=ph['data']['id']).first()
        policy_holder = {
            'id': str(policy_holder_object.id),
            'address': policy_holder_object.address,
        }
        response = self.policy_holder_service.update(policy_holder)
        PolicyHolder.objects.filter(id=ph['data']['id']).delete()
        self.assertEqual(
            (
                True,
                "Ok",
                "",
            ),
            (
                response['success'],
                response['message'],
                response['detail']
            )
        )

    def test_update_policy_holder_with_duplicated_display(self):
        self.POLICY_HOLDER['code'] = 'ddfdsffewdfd'

        first = self.policy_holder_service.create(self.POLICY_HOLDER)

        second = self.policy_holder_service.create({
            **self.POLICY_HOLDER,
            'trade_name': 'COTO2',
        })

        policy_holder = {'id': str(first['data']['id']), 'trade_name': second['data']['trade_name']}

        response = self.policy_holder_service.update(policy_holder)

        expected_error_message = PolicyHolderValidation.UNIQUE_DISPLAY_NAME_VALIDATION_ERROR \
            .format(self.POLICY_HOLDER['code'], second['data']['trade_name'])

        self.assertFalse(response['success'])
        self.assertTrue(expected_error_message in response['detail'])

    def test_policy_holder_update_without_id(self):
        policy_holder = {
            'address': {"region": "APAC", "street": "test"},
        }
        response = self.policy_holder_service.update(policy_holder)
        self.assertEqual(
            (
                False,
                "Failed to update PolicyHolder",
            ),
            (
                response['success'],
                response['message'],
            )
        )

    def test_policy_holder_create_delete(self):
        self.POLICY_HOLDER['code'] = 'qqeeyyaaf'
        response = self.policy_holder_service.create(self.POLICY_HOLDER)
        policy_holder_object = PolicyHolder.objects.filter(id=response['data']['id']).first()

        # version = policy_holder_object.version
        policy_holder = {
            'id': str(policy_holder_object.id),
        }
        response = self.policy_holder_service.delete(policy_holder)

        self.assertEqual(
            (
                True,
                "Ok",
                "",
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
            )
        )

    def test_policy_holder_insuree_create(self):
        policy_holder_insuree = {
            'policy_holder_id': str(self.test_policy_holder.id),
            'insuree_id': self.test_insuree.id,
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle.id),
            'last_policy_id': self.test_last_policy.id if self.test_last_policy else None
        }

        response = self.policy_holder_insuree_service.create(policy_holder_insuree)

        # tear down the test data
        PolicyHolderInsuree.objects.filter(id=response["data"]["id"]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                1,
                str(self.test_policy_holder.id),
                self.test_insuree.id,
                str(self.test_contribution_plan_bundle.id),
                self.test_last_policy.id if self.test_last_policy else None
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['version'],
                response['data']['policy_holder'],
                response['data']['insuree'],
                response['data']['contribution_plan_bundle'],
                response['data']['last_policy'],
            )
        )

    def test_policy_holder_insuree_create_without_fk(self):
        policy_holder_insuree = {
            'policy_holder_id': str(self.test_policy_holder.id),
        }

        response = self.policy_holder_insuree_service.create(policy_holder_insuree)
        self.assertEqual(
            (
                False,
                "Failed to create PolicyHolderInsuree",
            ),
            (
                response['success'],
                response['message'],
            )
        )

    def test_policy_holder_insuree_create_update(self):
        policy_holder_insuree = {
            'policy_holder_id': str(self.test_policy_holder.id),
            'insuree_id': self.test_insuree.id,
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle.id),
            'last_policy_id': self.test_last_policy.id if self.test_last_policy else None
        }

        response = self.policy_holder_insuree_service.create(policy_holder_insuree)

        policy_holder_insuree_object = PolicyHolderInsuree.objects.get(id=response['data']['id'])
        policy_holder_insuree = {
            'id': str(policy_holder_insuree_object.id),
            'insuree_id': self.test_insuree_to_change.id,
        }
        response = self.policy_holder_insuree_service.update(policy_holder_insuree)

        # tear down the test data
        PolicyHolderInsuree.objects.filter(id=response["data"]["id"]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                self.test_insuree_to_change.id,
                2,
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['insuree'],
                response['data']['version'],
            )
        )

    def test_policy_holder_insuree_update_without_changing_field(self):
        policy_holder_insuree = {
            'id': str(self.test_policy_holder_insuree.id),
            'insuree_id': self.test_insuree.id,
        }
        response = self.policy_holder_insuree_service.update(policy_holder_insuree)
        self.assertEqual(
            (
                True,
                "Ok",
                "",
            ),
            (
                response['success'],
                response['message'],
                response['detail']
            )
        )

    def test_policy_holder_insuree_update_without_id(self):
        policy_holder_insuree = {
            'insuree_id': self.test_insuree.id,
        }

        response = self.policy_holder_insuree_service.update(policy_holder_insuree)
        self.assertEqual(
            (
                False,
                "Failed to update PolicyHolderInsuree",
            ),
            (
                response['success'],
                response['message'],
            )
        )

    def test_policy_holder_insuree_replace(self):
        policy_holder_insuree = {
            'policy_holder_id': str(self.test_policy_holder.id),
            'insuree_id': self.test_insuree.id,
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle.id),
            'last_policy_id': self.test_last_policy.id if self.test_last_policy else None
        }

        response = self.policy_holder_insuree_service.create(policy_holder_insuree)
        id_replaced = response['data']['id']
        policy_holder_insuree_object = PolicyHolderInsuree.objects.get(id=response['data']['id'])
        policy_holder_insuree = {
            'uuid': str(policy_holder_insuree_object.id),
            'insuree_id': self.test_insuree_to_change.id,
            'contribution_plan_bundle_id': self.test_contribution_plan_bundle_to_replace.id
        }
        response = self.policy_holder_insuree_service.replace_policy_holder_insuree(policy_holder_insuree)

        # tear down the test data
        PolicyHolderInsuree.objects.filter(
            id__in=[id_replaced, response['uuid_new_object']]
        ).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                response["old_object"]["replacement_uuid"],
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response["uuid_new_object"],
            )
        )

    def test_policy_holder_insuree_replace_double(self):
        policy_holder_insuree = {
            'policy_holder_id': str(self.test_policy_holder.id),
            'insuree_id': self.test_insuree.id,
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle.id),
            'last_policy_id': self.test_last_policy.id if self.test_last_policy else None
        }

        response = self.policy_holder_insuree_service.create(policy_holder_insuree)

        policy_holder_insuree_object = PolicyHolderInsuree.objects.get(id=response['data']['id'])
        policy_holder_insuree = {
            'uuid': str(policy_holder_insuree_object.id),
            'insuree_id': self.test_insuree_to_change.id,
            'contribution_plan_bundle_id': self.test_contribution_plan_bundle_to_replace.id
        }
        id_first_object = str(policy_holder_insuree_object.id)
        response = self.policy_holder_insuree_service.replace_policy_holder_insuree(policy_holder_insuree)

        policy_holder_insuree_object = PolicyHolderInsuree.objects.get(id=response['uuid_new_object'])
        policy_holder_insuree = {
            'uuid': str(policy_holder_insuree_object.id),
            'insuree_id': self.test_insuree.id,
            'contribution_plan_bundle_id': self.test_contribution_plan_bundle.id
        }

        response = self.policy_holder_insuree_service.replace_policy_holder_insuree(policy_holder_insuree)

        # tear down the test data
        PolicyHolderInsuree.objects.filter(
            id__in=[str(policy_holder_insuree_object.id), response['uuid_new_object'], id_first_object]
        ).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                response["old_object"]["replacement_uuid"],
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response["uuid_new_object"],
            )
        )

    def test_policy_holder_contribution_plan_create(self):
        policy_holder_contribution_plan = {
            'policy_holder_id': str(self.test_policy_holder.id),
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle.id),
        }

        response = self.policy_holder_contribution_plan_service.create(policy_holder_contribution_plan)

        # tear down the test data
        PolicyHolderContributionPlan.objects.filter(id=response["data"]["id"]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                1,
                str(self.test_policy_holder.id),
                str(self.test_contribution_plan_bundle.id),
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['version'],
                response['data']['policy_holder'],
                response['data']['contribution_plan_bundle'],
            )
        )

    def test_policy_holder_contribution_plan_create_without_fk(self):
        policy_holder_contribution_plan = {
            'policy_holder_id': str(self.test_policy_holder.id),
        }

        response = self.policy_holder_contribution_plan_service.create(policy_holder_contribution_plan)
        self.assertEqual(
            (
                False,
                "Failed to create PolicyHolderContributionPlan",
            ),
            (
                response['success'],
                response['message'],
            )
        )

    def test_policy_holder_contribution_plan_replace(self):
        policy_holder_contribution_plan = {
            'policy_holder_id': str(self.test_policy_holder.id),
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle.id),
        }

        response = self.policy_holder_contribution_plan_service.create(policy_holder_contribution_plan)

        policy_holder_contribution_plan_object = PolicyHolderContributionPlan.objects.get(id=response['data']['id'])
        policy_holder_contribution_plan = {
            'uuid': str(policy_holder_contribution_plan_object.id),
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle_to_replace.id),
        }

        response = self.policy_holder_contribution_plan_service.replace_policy_holder_contribution_plan_bundle(
            policy_holder_contribution_plan
        )

        # tear down the test data
        PolicyHolderContributionPlan.objects.filter(
            id__in=[str(policy_holder_contribution_plan_object.id), response['uuid_new_object']]
        ).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                response["old_object"]["replacement_uuid"],
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response["uuid_new_object"],
            )
        )

    def test_policy_holder_contribution_plan_replace_double(self):
        policy_holder_contribution_plan = {
            'policy_holder_id': str(self.test_policy_holder.id),
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle.id),
        }

        response = self.policy_holder_contribution_plan_service.create(policy_holder_contribution_plan)

        policy_holder_contribution_plan_object = PolicyHolderContributionPlan.objects.get(id=response['data']['id'])
        policy_holder_contribution_plan = {
            'uuid': str(policy_holder_contribution_plan_object.id),
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle_to_replace.id),
        }
        id_first_object = str(policy_holder_contribution_plan_object.id)
        response = self.policy_holder_contribution_plan_service.replace_policy_holder_contribution_plan_bundle(
            policy_holder_contribution_plan
        )

        policy_holder_contribution_plan_object = PolicyHolderContributionPlan.objects.get(
            id=response['uuid_new_object'])
        policy_holder_contribution_plan = {
            'uuid': str(policy_holder_contribution_plan_object.id),
            'contribution_plan_bundle_id': str(self.test_contribution_plan_bundle.id),
        }
        response = self.policy_holder_contribution_plan_service.replace_policy_holder_contribution_plan_bundle(
            policy_holder_contribution_plan)

        # tear down the test data
        PolicyHolderContributionPlan.objects.filter(
            id__in=[str(policy_holder_contribution_plan_object.id), response['uuid_new_object'], id_first_object]
        ).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                response["old_object"]["replacement_uuid"],
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response["uuid_new_object"],
            )
        )
