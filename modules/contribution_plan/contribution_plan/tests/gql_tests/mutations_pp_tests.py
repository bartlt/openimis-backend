import datetime
import base64
from unittest import mock
from django.test import TestCase

import graphene
from contribution_plan.tests.helpers import *
from contribution_plan import schema as contribution_plan_schema
from calculation.calculation_rule import ContributionValuationRule
from core import datetime
from product.test_helpers import create_test_product
from graphene import Schema
from graphene.test import Client
from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext

class MutationTestPaymentPlan(openIMISGraphQLTestCase):

    class AnonymousUserContext:
        user = mock.Mock(is_anonymous=True)

    @classmethod
    def setUpClass(cls):
        super(MutationTestPaymentPlan, cls).setUpClass()
        if not User.objects.filter(username='Admin').exists():
            User.objects.create_superuser(username='Admin', password='S\/pe®Pąßw0rd™')
        cls.user = User.objects.filter(username='Admin').first()
        cls.user_context = BaseTestContext(cls.user)        
        cls.test_payment_plan = create_test_payment_plan()
        cls.test_calculation = ContributionValuationRule.uuid
        cls.test_calculation2 = ContributionValuationRule.uuid
        cls.test_product = create_test_product("PlanCode", custom_props={"insurance_period": 12, })
        cls.schema = Schema(
            query=contribution_plan_schema.Query,
            mutation=contribution_plan_schema.Mutation
        )
        cls.graph_client = Client(cls.schema)

    def test_payment_plan_create(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "XYZ",
            "name": "XYZ test name xyz - " + str(time_stamp),
            "benefitPlanId": self.test_product.id,
            "calculation": f"{self.test_calculation}",
            "periodicity": 12,
        }

        self.add_mutation("createPaymentPlan", input_param)
        result = self.find_by_exact_attributes_query(
            "paymentPlan",
            params=input_param,
        )["edges"]

        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        # tear down the test data
        PaymentPlan.objects.filter(id=f"{converted_id}").delete()

        self.assertEqual(
            (
                "XYZ test name xyz - " + str(time_stamp),
                "XYZ",
                1,
                12
            ),
            (
                result[0]['node']['name'],
                result[0]['node']['code'],
                result[0]['node']['version'],
                result[0]['node']['periodicity']
            )
        )

    def test_payment_plan_create_without_obligatory_fields(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "name": "XYZ test name xyz - " + str(time_stamp),
        }
        result_mutation = self.add_mutation("createPaymentPlan", input_param)
        self.assertEqual(True, 'errors' in result_mutation)

    def test_payment_plan_delete_single_deletion(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "XYZ deletion",
            "name": "XYZ test deletion xyz - " + str(time_stamp),
            "benefitPlanId": self.test_product.id,
            "calculation": f"{self.test_calculation}",
            "periodicity": 12,
        }
        self.add_mutation("createPaymentPlan", input_param)
        result = self.find_by_exact_attributes_query("paymentPlan", {**input_param, 'isDeleted': False})
        converted_id = base64.b64decode(result["edges"][0]['node']['id']).decode('utf-8').split(':')[1]
        input_param2 = {
            "uuids": [f"{converted_id}"],
        }
        self.add_mutation("deletePaymentPlan", input_param2)
        result2 = self.find_by_exact_attributes_query("paymentPlan", {**input_param, 'isDeleted': False})

        # tear down the test data
        PaymentPlan.objects.filter(id=f"{converted_id}").delete()

        self.assertEqual((1, 0), (result["totalCount"], result2["totalCount"]))

    def test_payment_plan_update_1_existing(self):
        id = self.test_payment_plan.id
        version = self.test_payment_plan.version
        input_param = {
            "id": f"{id}",
            "name": "XYZ test name xxxxx",
        }
        self.add_mutation("updatePaymentPlan", input_param)
        result = self.find_by_exact_attributes_query("paymentPlan", {**input_param})["edges"]
        self.test_payment_plan.version = result[0]['node']['version']

        self.assertEqual(
            ("XYZ test name xxxxx", version + 1),
            (result[0]['node']['name'], result[0]['node']['version'])
        )

    def find_by_exact_attributes_query(self, query_type, params, context=None):
        if "dateValidFrom" in params:
            params.pop('dateValidFrom')
        if "dateValidTo" in params:
            params.pop('dateValidTo')
        if "benefitPlanId" in params:
            params.pop('benefitPlanId')
        if "calculation" in params:
            params.pop('calculation')
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
            context = self.BaseTestContext(self.user)

        query_result = self.graph_client.execute(query, context=context)
        query_data = query_result['data']
        return query_data

    def add_mutation(self, mutation_type, input_params, context=None):

        mutation_result = self.send_mutation(mutation_type, input_params, cls.user_context.get_jwt()) 
        return mutation_result


    def execute_mutation(self, mutation, context=None):
        if context is None:
            context = self.BaseTestContext(self.user)

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
