from django.contrib.contenttypes.models import ContentType

from contribution_plan.models import ContributionPlanBundle, ContributionPlan, \
    ContributionPlanBundleDetails, PaymentPlan
from datetime import date

from core.models import User
from product.test_helpers import create_test_product
from calcrule_contribution_income_percentage.calculation_rule import ContributionValuationRule
from core.test_helpers import create_test_interactive_user


def create_test_contribution_plan_bundle(custom_props={}):
    user = __get_or_create_simple_contribution_plan_user()
    object_data = {
        'is_deleted': 0,
        'code': "Contribution Plan Bundle Code",
        'name': "Contribution Plan Bundle Name",
        'json_ext': {},
        **custom_props
    }

    contribution_plan_bundle = ContributionPlanBundle(**object_data)
    contribution_plan_bundle.save(user=user)

    return contribution_plan_bundle


def create_test_contribution_plan(product=None, calculation=ContributionValuationRule.uuid, custom_props={},
                                  periodicity=12):
    if not product:
        product = create_test_product("PlanCode", custom_props={"insurance_period": 12, })

    user = __get_or_create_simple_contribution_plan_user()

    object_data = {
        'is_deleted': False,
        'code': "%s-%s-%d" % (product.code, calculation, periodicity),
        'name': "Contribution Plan Name for %s and %s every %d" % (product.name, calculation, periodicity),
        'benefit_plan_type': ContentType.objects.get(model="product"),
        'benefit_plan_id': product.id,
        'periodicity': periodicity,
        'calculation': calculation,
        'json_ext': {},
        **custom_props
    }

    contribution_plan = ContributionPlan(**object_data)
    contribution_plan.save(username=user.username)

    return contribution_plan


def create_test_contribution_plan_bundle_details(contribution_plan_bundle=None, contribution_plan=None,
                                                 custom_props={}):
    if not contribution_plan_bundle:
        contribution_plan_bundle = create_test_contribution_plan_bundle()

    if not contribution_plan:
        contribution_plan = create_test_contribution_plan()

    user = __get_or_create_simple_contribution_plan_user()
    object_data = {
        'contribution_plan_bundle': contribution_plan_bundle,
        'contribution_plan': contribution_plan,
        'json_ext': {},
        'date_created': date(2010, 10, 30),
        'user_updated': user,
        'user_created': user,
        'date_valid_from': date(2010, 10, 30),
        'date_valid_to': None,
        'is_deleted': 0,
        **custom_props
    }

    contribution_plan_bundle_details = ContributionPlanBundleDetails(**object_data)
    contribution_plan_bundle_details.save(username=user.username)

    return contribution_plan_bundle_details


def create_test_payment_plan(product=None, calculation=ContributionValuationRule.uuid, custom_props={}, periodicity=1):
    if not product:
        product = create_test_product("PlanCode", custom_props={"insurance_period": 12, })

    user = __get_or_create_simple_contribution_plan_user()

    object_data = {
        'is_deleted': False,
        'code': "%s-%s-%d" % (product.code, calculation, periodicity),
        'name': "Payment Plan Name for %s and %s every %d" % (product.name, calculation, periodicity),
        'benefit_plan': product,
        'periodicity': periodicity,
        'calculation': calculation,
        'json_ext': {},
        **custom_props
    }

    payment_plan = PaymentPlan(**object_data)
    payment_plan.save(user=user)

    return payment_plan


def __get_or_create_simple_contribution_plan_user():

    return create_test_interactive_user(username='Admin23')
