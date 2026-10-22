import json

from core.models import filter_validity
from core.test_helpers import create_test_interactive_user, create_clerk_role
from django.conf import settings
from graphql_jwt.shortcuts import get_token
from location.test_helpers import (
    assign_user_districts,
    create_basic_test_locations,
    create_test_village
)
from rest_framework import status
from insuree.test_helpers import create_test_insuree
from policy.test_helpers import create_test_policy
from product.test_helpers import create_test_product
from payer.test_helpers import create_test_payer
from contribution.models import Premium, PayTypeChoices
import datetime

# from openIMIS import schema

from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext as DummyContext


class ContributionGQLTestCase(openIMISGraphQLTestCase):
    GRAPHQL_URL = f'/{settings.SITE_ROOT()}graphql'
    # This is required by some version of graphene but is never used. It should be set to the schema but the import
    # is shown as an error in the IDE, so leaving it as True.
    GRAPHQL_SCHEMA = True
    admin_user = None
    ca_user = None
    ca_token = None
    test_village = None
    test_insuree = None
    policy = None
    product = None
    payer = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_basic_test_locations()
        cls.test_village = create_test_village()
        cls.test_insuree = create_test_insuree(
            with_family=True,
            is_head=True,
            custom_props={'current_village': cls.test_village},
            family_custom_props={'location': cls.test_village}
        )
        cls.admin_user = create_test_interactive_user(username="testLocationAdmin")
        cls.admin_token = get_token(cls.admin_user, DummyContext(user=cls.admin_user))
        clerk_role = create_clerk_role()
        cls.ca_user = create_test_interactive_user(username="testLocationNoRight", roles=[clerk_role.id])
        cls.ca_token = get_token(cls.ca_user, DummyContext(user=cls.ca_user))
        cls.admin_dist_user = create_test_interactive_user(username="testLocationDist")
        assign_user_districts(cls.admin_dist_user, ["R1D1", "R2D1", "R2D2", "R2D1", cls.test_village.parent.parent.code])
        cls.admin_dist_token = get_token(cls.admin_dist_user, DummyContext(user=cls.admin_dist_user))
        cls.payer = create_test_payer()
        cls.product = create_test_product("ELI1")
        cls.policy = create_test_policy(
            cls.product,
            cls.test_insuree,
            custom_props={'value': 1000},
            link=True,
            valid=True
        )

    def test_add_funding(self):
        response = self.query(
            f'''
    mutation {{
      createPremium(
        input: {{
          uuid: "94a07513-87b9-469e-bb73-58eb717fee05"
          clientMutationId: "94a07513-87b9-469e-bb73-58eb717fee05"
          clientMutationLabel: "Create contribution"
          receipt: "ghfjgfhj"
          payDate: "2023-12-13"
          payType: "C"
          isPhotoFee: false
          amount: "4200"
          policyUuid: "{self.policy.uuid}"
              }}
      ) {{
        clientMutationId
        internalId
      }}
    }}

      ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json.loads(response.content)

        self.assertResponseNoErrors(response)
        # Wait

        response = self.query(
            '''
        {
        mutationLogs(clientMutationId: "94a07513-87b9-469e-bb73-58eb717fee05")
        {

        pageInfo { hasNextPage, hasPreviousPage, startCursor, endCursor}
        edges
        {
        node
        {
            id,status,error,clientMutationId,clientMutationLabel,clientMutationDetails,requestDateTime,jsonExt
        }
        }
        }
        }

        ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json.loads(response.content)
        self.assertResponseNoErrors(response)
        premium = Premium.objects.filter(uuid="94a07513-87b9-469e-bb73-58eb717fee05", *Premium.filter_validity()).first()
        self.assertIsNotNone(premium)
        self.assertEqual(premium.amount, 4200)
        # Modify premium

        response = self.query(
            f'''
    mutation {{
      updatePremium(
        input: {{
          uuid: "94a07513-87b9-469e-bb73-58eb717fee05"
          clientMutationId: "94a07513-87b9-469e-bb73-58eb717fee32"
          clientMutationLabel: "Create contribution"
          receipt: "ghfjgfhj"
          payDate: "2023-12-13"
          payType: "C"
          isPhotoFee: false
          amount: "4400"
          policyUuid: "{self.policy.uuid}"
              }}
      ) {{
        clientMutationId
        internalId
      }}
    }}

      ''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json.loads(response.content)
        self.assertResponseNoErrors(response)
        premium = Premium.objects.filter(uuid="94a07513-87b9-469e-bb73-58eb717fee05", *Premium.filter_validity()).first()
        self.assertIsNotNone(premium)
        self.assertEqual(premium.amount, 4400)

    def test_query_premium(self):
        premium = Premium.objects.create(**{
            'payer': self.payer,
            'pay_date': datetime.datetime.now(),
            'amount': "5000",
            'receipt': "test premium 1",
            'policy': self.policy,
            'pay_type': PayTypeChoices.BANK_TRANSFER,
            'audit_user_id': self.admin_user.id_for_audit
        })

        premium = Premium.objects.create(**{
            'payer': self.payer,
            'pay_date': datetime.datetime.now(),
            'amount': "10000",
            'receipt': "test premium 2",
            'policy': self.policy,
            'pay_type': PayTypeChoices.BANK_TRANSFER,
            'audit_user_id': self.admin_user.id_for_audit
        })
        response = self.query(
            f'''
           {{
            premiums(uuid: "{premium.uuid}")
            {{

          pageInfo {{ hasNextPage, hasPreviousPage, startCursor, endCursor}}
          edges
          {{
            node
            {{
              id,uuid,payDate,amount,payType,receipt,isPhotoFee,validityTo,clientMutationId,otherPremiums,payer{{id, uuid, name}},policy{{id, uuid, startDate, product{{name, code}}, expiryDate, value, sumPremiums, family{{id, uuid, headInsuree{{chfId, lastName, otherNames, dob}}}}
            }}
          }}
            }}
          }}
          }}
          ''', headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json.loads(response.content)

        self.assertResponseNoErrors(response)

    def test_query_premiums(self):
        response = self.query(
            '''
        {
          premiums(first: 10,orderBy: ["-payDate"])
          {
            totalCount

        pageInfo { hasNextPage, hasPreviousPage, startCursor, endCursor}
        edges
        {
          node
          {
            id,uuid,payDate,amount,payType,receipt,isPhotoFee,clientMutationId,validityTo,payer{id, uuid, name}
          }
        }
          }
        }''',
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"},
            variables={'first': 10, 'payerId': self.payer.uuid},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json.loads(response.content)

        self.assertResponseNoErrors(response)
