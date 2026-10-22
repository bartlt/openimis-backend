import datetime
import base64
import json
from unittest import mock
from django.test import TestCase

import graphene
from core.models import MutationLog
from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext
from contribution_plan.tests.helpers import *
from core.test_helpers import create_test_interactive_user
from contribution_plan import schema as contribution_plan_schema
from graphene import Schema
from graphene.test import Client


class MutationTestContributionPlanBundle(openIMISGraphQLTestCase):


    class AnonymousUserContext:
        user = mock.Mock(is_anonymous=True)

    @classmethod
    def setUpClass(cls):
        super(MutationTestContributionPlanBundle, cls).setUpClass()
        if not User.objects.filter(username='Admin').exists():
            User.objects.create_superuser(username='Admin', password='S\/pe®Pąßw0rd™')
        cls.user = create_test_interactive_user()
        cls.user_context = BaseTestContext(cls.user)

        cls.test_contribution_plan_bundle = create_test_contribution_plan_bundle(
            custom_props={'code': 'SuperContributionPlan mutations!'})

        cls.schema = Schema(
            query=contribution_plan_schema.Query,
            mutation=contribution_plan_schema.Mutation
        )

        cls.graph_client = Client(cls.schema)

    def test_contribution_plan_bundle_create(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "XYZ",
            "name": "XYZ test name xyz - " + str(time_stamp),
        }
        self.add_mutation("createContributionPlanBundle", input_param)
        result = self.find_by_exact_attributes_query("contributionPlanBundle", input_param)["edges"]

        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        # tear down the test data
        ContributionPlanBundle.objects.filter(id=f"{converted_id}").delete()

        self.assertEqual(
            ("XYZ test name xyz - " + str(time_stamp), "XYZ", 1),
            (result[0]['node']['name'], result[0]['node']['code'], result[0]['node']['version'])
        )

    def test_contribution_plan_bundle_create_without_obligatory_fields(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "name": "XYZ test name xyz - " + str(time_stamp),
        }
        result_mutation = self.send_mutation("createContributionPlanBundle", input_param, self.user_context.get_jwt(),  follow=False, allow_exceptions=False)
        self.assertEqual(True, 'errors' in result_mutation)

    def test_contribution_plan_bundle_delete_single_deletion(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "XYZ deletion",
            "name": "XYZ test deletion xyz - " + str(time_stamp),
        }
        self.add_mutation("createContributionPlanBundle", input_param)
        result = self.find_by_exact_attributes_query("contributionPlanBundle", {**input_param, 'isDeleted': False})
        converted_id = base64.b64decode(result["edges"][0]['node']['id']).decode('utf-8').split(':')[1]
        input_param2 = {
            "uuids": [f"{converted_id}"],
        }
        self.add_mutation("deleteContributionPlanBundle", input_param2)
        result2 = self.find_by_exact_attributes_query("contributionPlanBundle", {**input_param, 'isDeleted': False})

        # tear down the test data
        ContributionPlanBundle.objects.filter(id=f"{converted_id}").delete()

        self.assertEqual((1, 0), (result["totalCount"], result2["totalCount"]))

    def test_contribution_plan_bundle_update_1_existing(self):
        id = self.test_contribution_plan_bundle.id
        version = self.test_contribution_plan_bundle.version
        input_param = {
            "id": f"{id}",
            "name": "XYZ test name xxxxx",
        }
        self.add_mutation("updateContributionPlanBundle", input_param)
        result = self.find_by_exact_attributes_query("contributionPlanBundle", {**input_param})["edges"]
        self.test_contribution_plan_bundle.version = result[0]['node']['version']
        self.assertEqual(
            ("XYZ test name xxxxx", version + 1),
            (result[0]['node']['name'], result[0]['node']['version'])
        )

    def test_contribution_plan_bundle_update_2_without_changing_fields(self):
        id = self.test_contribution_plan_bundle.id
        version = self.test_contribution_plan_bundle.version
        input_param = {
            "id": f"{id}",
            "name": "XYZ test name xxxxx",
        }
        self.add_mutation("updateContributionPlanBundle", input_param)
        result = self.find_by_exact_attributes_query("contributionPlanBundle", input_param)["edges"]
        self.test_contribution_plan_bundle.version = result[0]['node']['version']
        self.assertEqual(
            ("XYZ test name xxxxx", version),
            (result[0]['node']['name'], result[0]['node']['version'])
        )

    def test_contribution_plan_bundle_update_3_existing_date_valid_from_change(self):
        id = self.test_contribution_plan_bundle.id
        version = self.test_contribution_plan_bundle.version
        input_param = {
            "id": f"{id}",
            "name": "XYZ test name xxxxx",
            "dateValidFrom": "2020-12-09"
        }
        self.add_mutation("updateContributionPlanBundle", input_param)
        result = self.find_by_exact_attributes_query("contributionPlanBundle", {**input_param})["edges"]
        self.test_contribution_plan_bundle.version = result[0]['node']['version']
        self.assertEqual(
            ("XYZ test name xxxxx", "2020-12-09T00:00:00"),
            (result[0]['node']['name'], result[0]['node']['dateValidFrom'])
        )

    def test_contribution_plan_bundle_update_4_date_valid_from_without_changing_fields(self):
        id = self.test_contribution_plan_bundle.id
        version = self.test_contribution_plan_bundle.version
        input_param = {
            "id": f"{id}",
            "name": "XYZ test name xxxxx",
            "dateValidFrom": "2020-12-09"
        }
        self.add_mutation("updateContributionPlanBundle", input_param)
        result = self.find_by_exact_attributes_query("contributionPlanBundle", input_param)["edges"]
        self.test_contribution_plan_bundle.version = result[0]['node']['version']
        self.assertEqual(
            ("XYZ test name xxxxx", version, "2020-12-09T00:00:00"),
            (result[0]['node']['name'], result[0]['node']['version'], result[0]['node']['dateValidFrom'])
        )

    def test_contribution_plan_bundle_update_5_update_field_code_not_editable(self):
        id = self.test_contribution_plan_bundle.id
        version = self.test_contribution_plan_bundle.version
        input_param = {
            "id": f"{id}",
            "code": "XYZ test name xxxxx",
        }
        result_mutation = self.send_mutation("updateContributionPlanBundle", input_param, self.user_context.get_jwt(), follow=False, allow_exceptions=False)
        self.assertEqual(True, 'errors' in result_mutation)

    def test_contribution_plan_bundle_update_6_without_id_field(self):
        id = self.test_contribution_plan_bundle.id
        version = self.test_contribution_plan_bundle.version
        input_param = {
            "name": "XYZ test name xxxxx",
        }
        result_mutation = self.send_mutation("updateContributionPlanBundle", input_param, self.user_context.get_jwt(), follow=False, allow_exceptions=False)
        self.assertEqual(True, 'errors' in result_mutation)

    def test_contribution_plan_bundle_create_date_valid_to_before_date_valid_from(self):
        time_stamp = datetime.datetime.now()
        code = "XYZ invalid range " + str(time_stamp)
        input_param = {
            "code": code,
            "name": "XYZ test invalid range xyz - " + str(time_stamp),
            "dateValidFrom": "2025-06-01",
            "dateValidTo": "2025-05-01",
        }
        mutation_result = self.send_mutation(
            "createContributionPlanBundle", input_param, self.user_context.get_jwt(),
            follow=False, allow_exceptions=False
        )
        internal_id = mutation_result['data']['createContributionPlanBundle']['internalId']
        mutation_log = MutationLog.objects.get(id=internal_id)

        self.assertEqual(MutationLog.ERROR, mutation_log.status)
        self.assertIn("date_valid_to_before_date_valid_from", mutation_log.error)
        self.assertEqual(0, ContributionPlanBundle.objects.filter(code=code).count())

    def test_contribution_plan_bundle_create_date_valid_to_after_date_valid_from(self):
        time_stamp = datetime.datetime.now()
        code = "XYZ valid range " + str(time_stamp)
        input_param = {
            "code": code,
            "name": "XYZ test valid range xyz - " + str(time_stamp),
            "dateValidFrom": "2025-05-01",
            "dateValidTo": "2025-06-01",
        }
        mutation_result = self.add_mutation("createContributionPlanBundle", input_param)
        node = mutation_result['data']['mutationLogs']['edges'][0]['node']

        self.assertEqual(MutationLog.SUCCESS, node['status'])
        self.assertEqual(1, ContributionPlanBundle.objects.filter(code=code).count())

        ContributionPlanBundle.objects.filter(code=code).delete()

    def test_contribution_plan_bundle_create_date_valid_to_without_date_valid_from(self):
        time_stamp = datetime.datetime.now()
        code = "XYZ default range " + str(time_stamp)
        input_param = {
            "code": code,
            "name": "XYZ test default range xyz - " + str(time_stamp),
            "dateValidTo": "2020-01-01",
        }
        mutation_result = self.send_mutation(
            "createContributionPlanBundle", input_param, self.user_context.get_jwt(),
            follow=False, allow_exceptions=False
        )
        internal_id = mutation_result['data']['createContributionPlanBundle']['internalId']
        mutation_log = MutationLog.objects.get(id=internal_id)

        self.assertEqual(MutationLog.ERROR, mutation_log.status)
        self.assertIn("date_valid_to_before_date_valid_from", mutation_log.error)
        self.assertEqual(0, ContributionPlanBundle.objects.filter(code=code).count())

    def test_contribution_plan_bundle_create_date_valid_to_ahead_without_date_valid_from(self):
        time_stamp = datetime.datetime.now()
        code = "XYZ default valid range " + str(time_stamp)
        date_valid_to = datetime.date.today() + datetime.timedelta(days=1)
        input_param = {
            "code": code,
            "name": "XYZ test default valid range xyz - " + str(time_stamp),
            "dateValidTo": f"{date_valid_to}",
        }
        mutation_result = self.add_mutation("createContributionPlanBundle", input_param)
        node = mutation_result['data']['mutationLogs']['edges'][0]['node']

        self.assertEqual(MutationLog.SUCCESS, node['status'])
        self.assertEqual(1, ContributionPlanBundle.objects.filter(code=code).count())

        ContributionPlanBundle.objects.filter(code=code).delete()

    def test_contribution_plan_bundle_update_7_date_valid_to_before_stored_date_valid_from(self):
        time_stamp = datetime.datetime.now()
        contribution_plan_bundle = create_test_contribution_plan_bundle(
            custom_props={
                'code': "XYZ stored range " + str(time_stamp),
                'date_valid_from': "2025-06-01",
            }
        )
        input_param = {
            "id": f"{contribution_plan_bundle.id}",
            "dateValidTo": "2025-05-01",
        }
        mutation_result = self.send_mutation(
            "updateContributionPlanBundle", input_param, self.user_context.get_jwt(),
            follow=False, allow_exceptions=False
        )
        internal_id = mutation_result['data']['updateContributionPlanBundle']['internalId']
        mutation_log = MutationLog.objects.get(id=internal_id)
        contribution_plan_bundle.refresh_from_db()

        self.assertEqual(MutationLog.ERROR, mutation_log.status)
        self.assertIn("date_valid_to_before_date_valid_from", mutation_log.error)
        self.assertIsNone(contribution_plan_bundle.date_valid_to)

        contribution_plan_bundle.mutations.all().delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()

    def test_contribution_plan_bundle_update_8_date_valid_to_after_stored_date_valid_from(self):
        time_stamp = datetime.datetime.now()
        contribution_plan_bundle = create_test_contribution_plan_bundle(
            custom_props={
                'code': "XYZ stored valid range " + str(time_stamp),
                'date_valid_from': "2025-05-01",
            }
        )
        input_param = {
            "id": f"{contribution_plan_bundle.id}",
            "dateValidTo": "2025-06-01",
        }
        mutation_result = self.add_mutation("updateContributionPlanBundle", input_param)
        node = mutation_result['data']['mutationLogs']['edges'][0]['node']
        contribution_plan_bundle.refresh_from_db()

        self.assertEqual(MutationLog.SUCCESS, node['status'])
        self.assertEqual(
            datetime.date(2025, 6, 1), contribution_plan_bundle.date_valid_to.date()
        )

        contribution_plan_bundle.mutations.all().delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()

    def find_by_id_query(self, query_type, id, context=None):
        query = F'''
        {{
            {query_type}(id:"{id}") {{
                totalCount
                edges {{
                  node {{
                    id
                    version
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

    def find_by_exact_attributes_query(self, query_type, params, foreign_key="", context=None):
        if "dateValidFrom" in params:
            params.pop('dateValidFrom')
        if "dateValidTo" in params:
            params.pop('dateValidTo')
        node_content_str = "\n".join(params.keys())
        query = F'''
        {{
            {query_type}({self.build_params(params)}) {{
                totalCount
                edges {{
                  node {{
                    {'id' if 'id' not in params else ''}
                    {node_content_str}
                    version
                    dateValidFrom
                    dateValidTo
                    replacementUuid
                    {foreign_key}
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

    def add_mutation(self, mutation_type, input_params, context=None):

        mutation_result = self.send_mutation(mutation_type, input_params, self.user_context.get_jwt()) 
        return mutation_result


    def execute_mutation(self, mutation, context=None):
        if context is None:
            context = self.user_context.get_request()

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
