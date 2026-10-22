import graphene

from core.schema import OpenIMISMutation, TinyInt
from core.gql.gql_mutations import ReplaceInputType


class ContributionPlanBundleInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=False)
    code = graphene.String(required=True, max_length=32)
    name = graphene.String(required=False, max_length=255)
    periodicity = graphene.Int(required=False)
    date_valid_from = graphene.Date(required=False)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)

class ContributionPlanBundleUpdateInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)
    name = graphene.String(required=False, max_length=255)
    periodicity = graphene.Int(required=False)
    json_ext = graphene.types.json.JSONString(required=False)
    date_valid_from = graphene.Date(required=False)
    date_valid_to = graphene.Date(required=False)


class ContributionPlanBundleReplaceInputType(ReplaceInputType):
    name = graphene.String(required=False, max_length=255)
    periodicity = graphene.Int(required=False)
    date_valid_from = graphene.Date(required=True)
    date_valid_to = graphene.Date(required=False)


class ContributionPlanInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=False)
    code = graphene.String(required=True, max_length=32)
    name = graphene.String(required=True, max_lenght=255)
    calculation = graphene.UUID(required=True)
    benefit_plan_type__model = graphene.String(required=False, max_lenght=255)
    benefit_plan_id = graphene.String(required=True)
    periodicity = graphene.Int(required=True)
    date_valid_from = graphene.Date(required=False)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)


class ContributionPlanUpdateInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)
    code = graphene.String(required=False, max_length=32)
    name = graphene.String(required=False, max_lenght=255)
    calculation = graphene.UUID(required=False)
    benefit_plan_type__model = graphene.String(required=False, max_lenght=255)
    benefit_plan_id = graphene.String(required=True)
    periodicity = graphene.Int(required=False)
    date_valid_from = graphene.Date(required=False)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)


class ContributionPlanReplaceInputType(ReplaceInputType):
    name = graphene.String(required=False, max_lenght=255)
    calculation = graphene.UUID(required=False)
    benefit_plan_type__model = graphene.String(required=False, max_lenght=255)
    benefit_plan_id = graphene.String(required=True)
    periodicity = graphene.Int(required=False)
    date_valid_from = graphene.Date(required=True)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)


class ContributionPlanBundleDetailsInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=False)
    contribution_plan_bundle_id = graphene.UUID(required=True)
    contribution_plan_id = graphene.UUID(required=True)
    date_valid_from = graphene.Date(required=False)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)


class ContributionPlanBundleDetailsUpdateInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)
    contribution_plan_bundle_id = graphene.UUID(required=False)
    contribution_plan_id = graphene.UUID(required=False)
    date_valid_from = graphene.Date(required=False)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)


class ContributionPlanBundleDetailsReplaceInputType(ReplaceInputType):
    contribution_plan_id = graphene.UUID(required=False)
    date_valid_from = graphene.Date(required=True)
    date_valid_to = graphene.Date(required=False)


class PaymentPlanInputType(ContributionPlanInputType):
    pass


class PaymentPlanUpdateInputType(ContributionPlanUpdateInputType):
    pass


class PaymentPlanReplaceInputType(ContributionPlanReplaceInputType):
    pass
