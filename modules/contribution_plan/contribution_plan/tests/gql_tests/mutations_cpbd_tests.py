import datetime
from unittest import mock

import graphene
from django.test import TestCase
from contribution_plan.tests.helpers import *
from contribution_plan import schema as contribution_plan_schema
from graphene import Schema
from graphene.test import Client
from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext
from core.test_helpers import create_test_interactive_user

class MutationTestContributionPlanBundleDetails(openIMISGraphQLTestCase):

    class AnonymousUserContext:
        user = mock.Mock(is_anonymous=True)

    @classmethod
    def setUpClass(cls):
        super(MutationTestContributionPlanBundleDetails, cls).setUpClass()
        if not User.objects.filter(username='Admin').exists():
            User.objects.create_superuser(username='Admin', password='S\/pe®Pąßw0rd™')
        cls.user = create_test_interactive_user()
        cls.user_context = BaseTestContext(cls.user)
        cls.test_contribution_plan_bundle = create_test_contribution_plan_bundle(
            custom_props={'code': 'SuperContributionPlan mutations!'})
        cls.test_contribution_plan = create_test_contribution_plan()
        cls.test_contribution_plan2 = create_test_contribution_plan()
        cls.test_contribution_plan_bundle_details = create_test_contribution_plan_bundle_details()

        cls.schema = Schema(
            query=contribution_plan_schema.Query,
            mutation=contribution_plan_schema.Mutation
        )

        cls.graph_client = Client(cls.schema)

    def test_contribution_plan_bundle_details_create_without_obligatory_fields(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "contributionPlanId": f"{self.test_contribution_plan_bundle.id}",
        }
        result_mutation = self.send_mutation("createContributionPlanBundleDetails", input_param, self.user_context.get_jwt(), allow_exceptions=False, follow=False) 
        self.assertEqual(True, 'errors' in result_mutation)

    def test_contribution_plan_bundle_details_update_1_existing_foreign_key(self):
        id = self.test_contribution_plan_bundle_details.id
        version = self.test_contribution_plan_bundle_details.version
        input_param = {
            "id": f"{id}",
            "contributionPlanId": f"{self.test_contribution_plan2.id}",
        }
        self.add_mutation("updateContributionPlanBundleDetails", input_param)
        result = self.find_by_id_query("contributionPlanBundleDetails", f"{id}")
        self.test_contribution_plan_bundle_details.version = result[0]['node']['version']
        self.assertEqual(version + 1, result[0]['node']['version'])

    def test_contribution_plan_bundle_details_update_2_without_changing_fields_foreign_key(self):
        id = self.test_contribution_plan_bundle_details.id
        version = self.test_contribution_plan_bundle_details.version
        input_param = {
            "id": f"{id}",
            "contributionPlanId": f"{self.test_contribution_plan2.id}",
        }
        self.send_mutation("updateContributionPlanBundleDetails", input_param, self.user_context.get_jwt(), follow=False, allow_exceptions=False)
        result = self.find_by_id_query("contributionPlanBundleDetails", f"{id}")
        self.test_contribution_plan_bundle_details.version = result[0]['node']['version']
        self.assertEqual(version, result[0]['node']['version'])

    def test_contribution_plan_update_3_without_id_field(self):
        id = self.test_contribution_plan.id
        version = self.test_contribution_plan.version
        input_param = {
            "name": "XYZ test name xxxxx",
        }
        result_mutation = self.send_mutation("updateContributionPlan", input_param, self.user_context.get_jwt(), follow=False, allow_exceptions=False)
        self.assertEqual(True, 'errors' in result_mutation)

    def find_by_id_query(self, query_type, id, context=None):
        query = F'''
        {{
            {query_type}(orderBy: ["dateCreated"], id:"{id}") {{
                totalCount
                edges {{
                  node {{
                    id
                    version
                    dateValidFrom
                    dateValidTo
                    replacementUuid
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
        if "dateValidFrom" in params:
            params.pop('dateValidFrom')
        if "dateValidTo" in params:
            params.pop('dateValidTo')
        if "contributionPlanId" in params:
            params.pop('contributionPlanId')
        if "contributionPlanBundleId" in params:
            params.pop('contributionPlanBundleId')

        node_content_str = "\n".join(params.keys())
        query = F'''
        {{
            {query_type}(orderBy: ["dateCreated"], {self.build_params(params)}) {{
                totalCount
                edges {{
                  node {{
                    {'id' if 'id' not in params else ''}
                    version
                    dateValidFrom
                    dateValidTo
                    replacementUuid
                  }}
                  cursor
                }}
          }}
        }}
        '''
        query_result = self.execute_query(query, context=context)
        records = query_result[query_type]
        return records

    def execute_query(self, query, context=None):
        if context is None:
            context = self.user_context.get_request()

        query_result = self.graph_client.execute(query, context=context)
        query_data = query_result['data']
        return query_data

    def add_mutation(self, mutation_type, input_params, context=None, allow_exceptions=True):

        mutation_result = self.send_mutation(mutation_type, input_params, self.user_context.get_jwt(), allow_exceptions=allow_exceptions) 
        return mutation_result

 

        mutation_result = self.graph_client.execute(mutation, context=context)
        return mutation_result

    def build_params(self, params):
        def wrap_arg(v):
            if isinstance(v, str):
                return F'"{v}"'
            if isinstance(v, list):
                return json.dumps(v)
            if isinstance(v, bool):
                return str(v).lower()
            if isinstance(v, datetime.date):
                return graphene.DateTime.serialize(
                    datetime.datetime.fromordinal(v.toordinal()))
            return v

        params_as_args = [f'{k}:{wrap_arg(v)}' for k, v in params.items()]
        return ", ".join(params_as_args)
