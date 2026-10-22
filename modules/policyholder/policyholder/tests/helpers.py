from contribution_plan.tests.helpers import create_test_contribution_plan_bundle
from core.test_helpers import create_test_interactive_user
from insuree.test_helpers import create_test_insuree
from location.models import Location
from policy.test_helpers import create_test_policy

from policyholder.models import PolicyHolder, PolicyHolderInsuree, PolicyHolderUser

from product.test_helpers import create_test_product

PH_DATA = {
    'code': 'PHCode',
    'trade_name': 'CompanyTest',
}


def create_test_policy_holder(locations=None, custom_props={}, user=None):
    user = user or __get_or_create_simple_policy_holder_user()

    object_data = {
        **PH_DATA,
        **custom_props
    }

    policy_holder = PolicyHolder(**object_data)
    if locations:
        policy_holder.locations_uuid = locations
    else:
        location = Location.objects.order_by('id').first()
        policy_holder.locations_uuid = location
    policy_holder.save(user=user)

    return policy_holder


def create_test_policy_holder_insuree(policy_holder=None, insuree=None, contribution_plan_bundle=None,
                                      last_policy=None, custom_props={}):
    if not policy_holder:
        policy_holder = create_test_policy_holder()
    if not insuree:
        insuree = create_test_insuree()
    if not contribution_plan_bundle:
        contribution_plan_bundle = create_test_contribution_plan_bundle()
    if last_policy is True:
        last_policy = create_test_policy(
            product=create_test_product("TestCode", custom_props={"insurance_period": 12, }),
            insuree=insuree)

    user = __get_or_create_simple_policy_holder_user()

    object_data = {
        'policy_holder': policy_holder,
        'insuree': insuree,
        'contribution_plan_bundle': contribution_plan_bundle,
        'last_policy': last_policy,
        'json_ext': {},
        **custom_props
    }

    policy_holder_insuree = PolicyHolderInsuree(**object_data)
    policy_holder_insuree.save(user=user)

    return policy_holder_insuree


def create_test_policy_holder_user(user=None, policy_holder=None, custom_props={}):
    if not user:
        user = __get_or_create_simple_policy_holder_user()

    if not policy_holder:
        policy_holder = create_test_policy_holder()

    # audit_user = __get_or_create_simple_policy_holder_user()

    object_data = {
        'user': user,
        'policy_holder': policy_holder,
        'json_ext': {},
        **custom_props
    }

    policy_holder_user = PolicyHolderUser(**object_data)
    policy_holder_user.save(user=user)

    return policy_holder_user


def __get_or_create_simple_policy_holder_user():
    return create_test_interactive_user(username='AdminPH')
