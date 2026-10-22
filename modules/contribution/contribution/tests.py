# Create your tests here.
from django.test import TestCase

from contribution.test_helpers import create_test_premium
from core.test_helpers import create_test_officer
from insuree.test_helpers import create_test_insuree
from policy.models import Policy
from policy.test_helpers import create_test_policy2
from product.test_helpers import create_test_product


class TaskGroupServiceTest(TestCase):
    def test_helper(self):
        create_test_officer(custom_props={"code": "TSTSIMP1"})
        insuree = create_test_insuree(custom_props={"chf_id": "paysimp"})
        product = create_test_product("ELI1")
        (policy, insuree_policy) = create_test_policy2(product, insuree, custom_props={
            "value": 1000, "status": Policy.STATUS_IDLE})
        create_test_premium(policy_id=policy.id, with_payer=False)
