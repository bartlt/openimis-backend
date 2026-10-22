from core.rights_role_test_case import RightsRoleGraphQLTestCase
from core.test_helpers import (
    create_enrolment_officer_role,
    create_right_only_user,
    create_role_user,
    create_test_officer,
)
from location.test_helpers import create_basic_test_locations, create_test_village
from payer.test_helpers import create_test_payer


PAYERS_QUERY = """
query {
  payers(first: 5) {
    edges { node { id uuid name } }
  }
}
"""


class PayerRightsTests(RightsRoleGraphQLTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_basic_test_locations()
        create_test_payer()

    def test_query_payers_right(self):
        allowed = create_right_only_user(
            "r_payr_q", ["gql_query_payers_perms"], district_codes=self.DISTRICT_CODES
        )
        denied = create_right_only_user("r_payr_q_no", [], district_codes=self.DISTRICT_CODES)
        self.assert_gql_ok(allowed, PAYERS_QUERY)
        self.assert_gql_unauthorized(denied, PAYERS_QUERY)


class PayerRoleTests(RightsRoleGraphQLTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_basic_test_locations()
        create_test_payer()
        village = create_test_village()
        officer = create_test_officer(villages=[village], custom_props={"code": "PAYEO"})
        cls.eo = create_role_user(
            "pay_eo",
            create_enrolment_officer_role(),
            district_codes=cls.DISTRICT_CODES + [village.parent.parent.code],
            officer=officer,
        )

    def test_enrolment_officer_can_query_payers(self):
        self.assert_user_has_named_perms(self.eo, ["gql_query_payers_perms"])
        self.assert_gql_ok(self.eo, PAYERS_QUERY)
