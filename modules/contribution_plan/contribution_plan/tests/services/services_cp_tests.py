from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from contribution_plan.services import ContributionPlanService, \
    ContributionPlanBundleService, \
    ContributionPlanBundleDetails as ContributionPlanBundleDetailsService, PaymentPlan as PaymentPlanService
from contribution_plan.models import ContributionPlan, ContributionPlanBundle, \
    ContributionPlanBundleDetails, PaymentPlan
from calcrule_contribution_income_percentage.calculation_rule import ContributionValuationRule
from core.models import User
from contribution_plan.tests.helpers import create_test_contribution_plan, \
    create_test_contribution_plan_bundle
from product.models import Product
from product.test_helpers import create_test_product


class ServiceTestContributionPlan(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ServiceTestContributionPlan, cls).setUpClass()
        if not User.objects.filter(username='Admin').exists():
            User.objects.create_superuser(username='Admin', password='S\/pe®Pąßw0rd™')
        cls.user = User.objects.filter(username='Admin').first()
        cls.contribution_plan_service = ContributionPlanService(cls.user)
        cls.contribution_plan_bundle_service = ContributionPlanBundleService(cls.user)
        cls.contribution_plan_bundle_details_service = ContributionPlanBundleDetailsService(cls.user)
        cls.payment_plan_service = PaymentPlanService(cls.user)
        cls.test_product = create_test_product("PlanCode", custom_props={"insurance_period": 12, })
        cls.test_product2 = create_test_product("PC", custom_props={"insurance_period": 6})
        cls.contribution_plan_bundle = create_test_contribution_plan_bundle()
        cls.contribution_plan = create_test_contribution_plan()
        cls.contribution_plan2 = create_test_contribution_plan()
        cls.calculation = ContributionValuationRule.uuid
        cls.product_content_type = ContentType.objects.get_for_model(Product)

    def test_contribution_plan_create(self):
        contribution_plan = {
            'code': "CP SERVICE",
            'name': "Contribution Plan Name Service",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.contribution_plan_service.create(contribution_plan)

        # tear down the test data
        ContributionPlan.objects.filter(id=response["data"]["id"]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                "CP SERVICE",
                "Contribution Plan Name Service",
                1,
                6,
                str(self.test_product.id),
                str(self.calculation),
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['code'],
                response['data']['name'],
                response['data']['version'],
                response['data']['periodicity'],
                response['data']['benefit_plan_id'],
                response['data']['calculation'],
            )
        )

    def test_contribution_plan_create_without_obligatory_field(self):
        contribution_plan = {
            'code': "CP SERVICE",
            'name': "Contribution Plan Name Service",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.contribution_plan_service.create(contribution_plan)
        self.assertEqual(
            (
                False,
                "Failed to create ContributionPlan",
            ),
            (
                response['success'],
                response['message'],
            )
        )

    def test_contribution_plan_create_update(self):
        contribution_plan = {
            'code': "CP SERUPD",
            'name': "CP for update",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.contribution_plan_service.create(contribution_plan)
        contribution_plan_object = ContributionPlan.objects.get(id=response['data']['id'])
        contribution_plan_to_update = {
            'id': str(contribution_plan_object.id),
            'periodicity': 12,
        }
        response = self.contribution_plan_service.update(contribution_plan_to_update)

        # tear down the test data
        ContributionPlan.objects.filter(id=contribution_plan_object.id).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                12,
                2,
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['periodicity'],
                response['data']['version'],
            )
        )

    def test_contribution_plan_create_update_benefit_plan(self):
        contribution_plan = {
            'code': "CP SERUPD",
            'name': "CP for update",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.contribution_plan_service.create(contribution_plan)
        contribution_plan_object = ContributionPlan.objects.get(id=response['data']['id'])

        contribution_plan_to_update = {
            'id': str(contribution_plan_object.id),
            'periodicity': 3,
            'benefit_plan_id': self.test_product2.id,
            'benefit_plan_type': self.product_content_type,
        }
        response = self.contribution_plan_service.update(contribution_plan_to_update)

        # tear down the test data
        ContributionPlan.objects.filter(id=contribution_plan_object.id).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                3,
                2,
                str(self.test_product2.id),
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['periodicity'],
                response['data']['version'],
                response['data']['benefit_plan_id']
            )
        )

    def test_contribution_plan_update_without_changing_field(self):
        contribution_plan = {
            'code': "CPUWCF",
            'name': "CP for update without changing fields",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response_create = self.contribution_plan_service.create(contribution_plan)
        contribution_plan_to_update = {
            'id': str(response_create["data"]["id"]),
            'periodicity': 6,
        }
        response = self.contribution_plan_service.update(contribution_plan_to_update)

        # tear down the test data
        ContributionPlan.objects.filter(id=response_create["data"]["id"]).delete()

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

    def test_contribution_plan_update_without_id(self):
        contribution_plan = {
            'periodicity': 6,
        }
        response = self.contribution_plan_service.update(contribution_plan)
        self.assertEqual(
            (
                False,
                "Failed to update ContributionPlan",
            ),
            (
                response['success'],
                response['message'],
            )
        )

    def test_contribution_plan_replace(self):
        contribution_plan = {
            'code': "CP SERUPD",
            'name': "CP for update",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.contribution_plan_service.create(contribution_plan)
        contribution_plan_object = ContributionPlan.objects.get(id=response['data']['id'])

        contribution_plan_to_replace = {
            'uuid': str(contribution_plan_object.id),
            'periodicity': 3,
        }

        response = self.contribution_plan_service.replace(contribution_plan_to_replace)
        contribution_plan_new_replaced_object = ContributionPlan.objects.get(id=response['uuid_new_object'])

        # tear down the test data
        ContributionPlan.objects.filter(
            id__in=[contribution_plan_object.id, contribution_plan_new_replaced_object.id]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                response["old_object"]["replacement_uuid"],
                3
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response["uuid_new_object"],
                contribution_plan_new_replaced_object.periodicity
            )
        )

    def test_contribution_plan_replace_product(self):
        contribution_plan = {
            'code': "CP SERUPD",
            'name': "CP for update",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.contribution_plan_service.create(contribution_plan)
        contribution_plan_object = ContributionPlan.objects.get(id=response['data']['id'])

        contribution_plan_to_replace = {
            'uuid': str(contribution_plan_object.id),
            'periodicity': 3,
            'benefit_plan_id': self.test_product2.id,
            'benefit_plan_type': self.product_content_type,
        }

        response = self.contribution_plan_service.replace(contribution_plan_to_replace)
        contribution_plan_new_replaced_object = ContributionPlan.objects.get(id=response['uuid_new_object'])

        # tear down the test data
        ContributionPlan.objects.filter(
            id__in=[contribution_plan_object.id, contribution_plan_new_replaced_object.id]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                response["old_object"]["replacement_uuid"],
                3,
                self.test_product2.id
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response["uuid_new_object"],
                contribution_plan_new_replaced_object.periodicity,
                contribution_plan_new_replaced_object.benefit_plan.id,
            )
        )

    def test_contribution_plan_replace_double(self):
        contribution_plan = {
            'code': "CP SERUPD",
            'name': "CP for update",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.contribution_plan_service.create(contribution_plan)

        contribution_plan_object = ContributionPlan.objects.get(id=response['data']['id'])
        contribution_plan_to_replace = {
            'uuid': str(contribution_plan_object.id),
            'periodicity': 3,
        }
        response = self.contribution_plan_service.replace(contribution_plan_to_replace)
        contribution_plan_new_replaced_object = ContributionPlan.objects.get(id=response['uuid_new_object'])

        contribution_plan_object = ContributionPlan.objects.get(id=response['uuid_new_object'])
        contribution_plan_to_replace_again = {
            'uuid': str(contribution_plan_object.id),
            'periodicity': 2,
            'benefit_plan_id': self.test_product2.id,
            'benefit_plan_type': self.product_content_type,
        }

        response = self.contribution_plan_service.replace(contribution_plan_to_replace_again)
        contribution_plan_new_replaced_object2 = ContributionPlan.objects.get(id=response['uuid_new_object'])

        # tear down the test data
        ContributionPlan.objects.filter(
            id__in=[contribution_plan_object.id, contribution_plan_new_replaced_object.id,
                    contribution_plan_new_replaced_object2.id]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                response["old_object"]["replacement_uuid"],
                3,
                2,
                self.test_product2.id,
                1,
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response["uuid_new_object"],
                contribution_plan_new_replaced_object.periodicity,
                contribution_plan_new_replaced_object2.periodicity,
                contribution_plan_new_replaced_object2.benefit_plan.id,
                contribution_plan_new_replaced_object2.version
            )
        )

    def test_contribution_plan_bundle_create(self):
        contribution_plan_bundle = {
            'code': "CPB1",
            'name': "CPB test",
            'periodicity': 6,
        }

        response = self.contribution_plan_bundle_service.create(contribution_plan_bundle)

        # tear down the test data
        ContributionPlanBundle.objects.filter(id=response['data']['id']).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                "CPB1",
                "CPB test",
                1,
                6,
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['code'],
                response['data']['name'],
                response['data']['version'],
                response['data']['periodicity'],
            )
        )

    def test_contribution_plan_bundle_create_update(self):
        contribution_plan_bundle = {
            'code': "CPB1",
            'name': "CPB test",
            'periodicity': 6,
        }

        response = self.contribution_plan_bundle_service.create(contribution_plan_bundle)
        contribution_plan_bundle_object = ContributionPlanBundle.objects.get(id=response['data']['id'])
        contribution_plan_bundle_to_update = {
            'id': str(contribution_plan_bundle_object.id),
            'name': "name updated",
            'periodicity': 4,
        }
        response = self.contribution_plan_bundle_service.update(contribution_plan_bundle_to_update)

        # tear down the test data
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle_object.id).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                "name updated",
                2,
                4,
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['name'],
                response['data']['version'],
                response['data']['periodicity'],
            )
        )

    def test_contribution_plan_bundle_update_without_changing_field(self):
        contribution_plan_bundle = {
            'code': "CPB1",
            'name': "name not changed",
            'periodicity': 6,
        }

        response = self.contribution_plan_bundle_service.create(contribution_plan_bundle)
        contribution_plan_bundle_object = ContributionPlanBundle.objects.get(id=response['data']['id'])
        contribution_plan_bundle_to_update = {
            'id': str(contribution_plan_bundle_object.id),
            'name': "name not changed",
        }

        response = self.contribution_plan_bundle_service.update(contribution_plan_bundle_to_update)

        # tear down the test data
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle_object.id).delete()

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

    def test_contribution_plan_bundle_update_without_id(self):
        contribution_plan_bundle = {
            'name': "XXXXXX",
        }
        response = self.contribution_plan_bundle_service.update(contribution_plan_bundle)
        self.assertEqual(
            (
                False,
                "Failed to update ContributionPlanBundle",
            ),
            (
                response['success'],
                response['message'],
            )
        )

    def test_contribution_plan_bundle_replace(self):
        contribution_plan_bundle = {
            'code': "CPBRep",
            'name': "replacement",
            'periodicity': 6,
        }

        response = self.contribution_plan_bundle_service.create(contribution_plan_bundle)
        contribution_plan_bundle_object = ContributionPlanBundle.objects.get(id=response['data']['id'])

        contribution_plan_bundle_to_replace = {
            'uuid': str(contribution_plan_bundle_object.id),
            "name": "Rep XX",
            'periodicity': 3,
        }

        response = self.contribution_plan_bundle_service.replace(contribution_plan_bundle_to_replace)
        contribution_plan_bundle_new_replaced_object = ContributionPlanBundle.objects.get(
            id=response['uuid_new_object'])

        # tear down the test data
        ContributionPlanBundle.objects.filter(
            id__in=[contribution_plan_bundle_object.id, contribution_plan_bundle_new_replaced_object.id]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                response["old_object"]["replacement_uuid"],
                "Rep XX",
                3
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response["uuid_new_object"],
                contribution_plan_bundle_new_replaced_object.name,
                contribution_plan_bundle_new_replaced_object.periodicity
            )
        )

    def test_contribution_plan_bundle_details_create(self):
        contribution_plan_bundle_details = {
            'contribution_plan_bundle_id': str(self.contribution_plan_bundle.id),
            'contribution_plan_id': str(self.contribution_plan.id),
        }

        response = self.contribution_plan_bundle_details_service.create(contribution_plan_bundle_details)

        # tear down the test data
        ContributionPlanBundleDetails.objects.filter(id=response["data"]["id"]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                1,
                str(self.contribution_plan.id),
                str(self.contribution_plan_bundle.id),
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['version'],
                response['data']['contribution_plan'],
                response['data']['contribution_plan_bundle'],
            )
        )

    def test_contribution_plan_bundle_details_update(self):
        contribution_plan_bundle_details = {
            'contribution_plan_bundle_id': str(self.contribution_plan_bundle.id),
            'contribution_plan_id': str(self.contribution_plan.id),
        }

        response = self.contribution_plan_bundle_details_service.create(contribution_plan_bundle_details)
        contribution_plan_bundle_details_object = ContributionPlanBundleDetails.objects.get(id=response['data']['id'])

        contribution_plan = {
            'code': "CP SERUPD",
            'name': "CP for update",
            'benefit_plan_id': str(self.test_product.id),
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.contribution_plan_service.create(contribution_plan)
        contribution_plan_object = ContributionPlan.objects.get(id=response['data']['id'])

        contribution_plan_bundle_details_to_update = {
            'id': str(contribution_plan_bundle_details_object.id),
            'contribution_plan_id': str(contribution_plan_object.id),
        }

        response = self.contribution_plan_bundle_details_service.update(contribution_plan_bundle_details_to_update)

        # tear down the test data
        ContributionPlanBundleDetails.objects.filter(id=contribution_plan_bundle_details_object.id).delete()
        ContributionPlan.objects.filter(id=contribution_plan_object.id).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                2,
                str(contribution_plan_object.id),
                str(self.contribution_plan_bundle.id),
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['version'],
                response['data']['contribution_plan'],
                response['data']['contribution_plan_bundle'],
            )
        )

    def test_payment_plan_create(self):
        payment_plan = {
            'code': "PP SERVICE",
            'name': "Payment Plan Name Service",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.payment_plan_service.create(payment_plan)

        # tear down the test data
        PaymentPlan.objects.filter(id=response["data"]["id"]).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                "PP SERVICE",
                "Payment Plan Name Service",
                1,
                6,
                str(self.test_product.id),
                str(self.calculation),
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['code'],
                response['data']['name'],
                response['data']['version'],
                response['data']['periodicity'],
                response['data']['benefit_plan_id'],
                response['data']['calculation'],
            )
        )

    def test_payment_plan_create_update(self):
        payment_plan = {
            'code': "PP SERUPD",
            'name': "PP for update",
            'benefit_plan_id': self.test_product.id,
            'benefit_plan_type': self.product_content_type,
            'periodicity': 6,
            'calculation': str(self.calculation),
            'json_ext': {},
        }

        response = self.payment_plan_service.create(payment_plan)
        payment_plan_object = PaymentPlan.objects.get(id=response['data']['id'])
        payment_plan_to_update = {
            'id': str(payment_plan_object.id),
            'periodicity': 12,
        }
        response = self.payment_plan_service.update(payment_plan_to_update)

        # tear down the test data
        PaymentPlan.objects.filter(id=payment_plan_object.id).delete()

        self.assertEqual(
            (
                True,
                "Ok",
                "",
                12,
                2,
            ),
            (
                response['success'],
                response['message'],
                response['detail'],
                response['data']['periodicity'],
                response['data']['version'],
            )
        )
