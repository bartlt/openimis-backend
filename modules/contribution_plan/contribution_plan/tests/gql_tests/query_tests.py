import graphene
import datetime
import base64

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from graphene import Schema
from graphene.test import Client
from unittest import mock
from uuid import UUID
from core.test_helpers import create_test_interactive_user
from contribution_plan.tests.helpers import *
from contribution_plan import schema as contribution_plan_schema
from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext


class QueryTest(TestCase):

    class AnonymousUserContext:
        user = AnonymousUser()

    @classmethod
    def setUpClass(cls):
        super(QueryTest, cls).setUpClass()
        cls.test_contribution_plan_bundle = create_test_contribution_plan_bundle(
            custom_props={'code': 'SuperContributionPlan!'})
        cls.test_contribution_plan = create_test_contribution_plan()
        cls.test_contribution_plan_details = create_test_contribution_plan_bundle_details()
        cls.test_payment_plan = create_test_payment_plan()
        cls.user = create_test_interactive_user()
        cls.user_context = BaseTestContext(cls.user)
        cls.schema = Schema(
            query=contribution_plan_schema.Query,
            mutation=contribution_plan_schema.Mutation
        )

        cls.graph_client = Client(cls.schema)

    def test_find_contribution_plan_bundle_existing(self):
        id = self.test_contribution_plan_bundle.id
        result = self.find_by_id_query("contributionPlanBundle", id)
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contribution_plan_existing(self):
        id = self.test_contribution_plan.id
        result = self.find_by_id_query("contributionPlan", id)
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_payment_plan_existing(self):
        id = self.test_payment_plan.id
        result = self.find_by_id_query("paymentPlan", id)
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contribution_plan_details_existing(self):
        id = self.test_contribution_plan_details.id
        result = self.find_by_id_query("contributionPlanBundleDetails", id)
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contribution_plan_bundle_by_params(self):
        expected = self.test_contribution_plan_bundle
        params = {
            'version': expected.version,
            'isDeleted': True if expected.is_deleted else False,
            'code': expected.code,
            'name': expected.name,
        }
        result = self.find_by_exact_attributes_query("contributionPlanBundle", params)
        self.assertDictEqual(result[0]['node'], params)

    def test_find_contribution_plan_bundle_existing_anonymous_user(self):
        result_cpb = self.find_by_id_query_anonymous_context(
            "contributionPlanBundle",
            self.test_contribution_plan_bundle.id,
        )
        result_cpbd = self.find_by_id_query_anonymous_context(
            "contributionPlanBundleDetails",
            self.test_contribution_plan_details.id,
        )

        self.assertEqual(result_cpb[0]['message'], 'Unauthorized')
        self.assertEqual(result_cpbd[0]['message'], 'Unauthorized')

    def test_find_contribution_plan_details_by_contribution(self):
        details_contribution_bundle_id = self.test_contribution_plan_details.contribution_plan_bundle.id
        details_contribution_plan_id = self.test_contribution_plan_details.contribution_plan.id
        id = self.test_contribution_plan_details.id
        query = F'''
        {{
            contributionPlanBundleDetails(
                contributionPlan_Id:"{details_contribution_plan_id}",
                contributionPlanBundle_Id:"{details_contribution_bundle_id}") {{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        '''
        query_result = self.execute_query(query)
        result = query_result['contributionPlanBundleDetails']['edges'][0]['node']
        converted_id = base64.b64decode(result['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def find_by_id_query(self, query_type, id, context=None):
        query = F'''
        {{
            {query_type}(id:"{id}") {{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        '''
        query_result = self.execute_query(query, context=context)
        records = query_result[query_type]['edges']

        if len(records) > 1:
            raise ValueError(F"Ambiguous id {id} for query {query_type}")

        return records

    def find_by_exact_attributes_query(self, query_type, params, context=None):
        node_content_str = "\n".join(params.keys())
        query = F'''
        {{
            {query_type}({self.build_params(params)}) {{
                totalCount
                edges {{
                  node {{
                    {node_content_str}
                  }}
                  cursor
                }}
          }}
        }}
        '''
        query_result = self.execute_query(query, context=context)
        records = query_result[query_type]['edges']
        return records

    def find_by_id_query_anonymous_context(self, query_type, id):
        query = F'''
        {{
            {query_type}(id:"{id}") {{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        '''
        query_result = self.execute_query_anonymous_context(query)
        return query_result

    def execute_query(self, query, context=None):
        if context is None:
            context = self.user_context.get_request()

        query_result = self.graph_client.execute(query, context=context)
        query_data = query_result['data']
        return query_data

    def execute_query_anonymous_context(self, query):
        query_result = self.graph_client.execute(query, context_value=self.AnonymousUserContext())
        query_data = query_result['errors']
        return query_data

    def build_params(self, params):
        def wrap_arg(v):
            if isinstance(v, str):
                return F'"{v}"'
            if isinstance(v, bool):
                return str(v).lower()
            if isinstance(v, datetime.date):
                return graphene.DateTime.serialize(
                    datetime.datetime.fromordinal(v.toordinal()))
                # return F'"{datetime.datetime.fromordinal()}"'
            return v  # if isinstance(v, numbers.Number) else F'"{v}"'

        params_as_args = [f'{k}:{wrap_arg(v)}' for k, v in params.items()]
        return ", ".join(params_as_args)
