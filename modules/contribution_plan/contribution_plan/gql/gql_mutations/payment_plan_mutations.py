from django.contrib.contenttypes.models import ContentType

from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation import BaseMutation, BaseDeleteMutation, BaseReplaceMutation, \
    BaseHistoryModelCreateMutationMixin, BaseHistoryModelUpdateMutationMixin, \
    BaseHistoryModelDeleteMutationMixin, BaseHistoryModelReplaceMutationMixin
from contribution_plan.services import PaymentPlan as PaymentPlanService
from contribution_plan.gql.gql_mutations import PaymentPlanInputType, PaymentPlanUpdateInputType, \
    PaymentPlanReplaceInputType
from contribution_plan.apps import ContributionPlanConfig
from contribution_plan.models import PaymentPlan
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from contribution_plan.gql.gql_mutations.validation import (
    validate_date_validity_range,
    validate_date_validity_range_on_create,
    validate_date_validity_range_on_update,
)


class CreatePaymentPlanMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "PaymentPlanMutation"
    _mutation_module = "contribution_plan"
    _model = PaymentPlan

    @classmethod
    def create_object(cls, user, object_data):
        benefit_plan_type__model = object_data.pop('benefit_plan_type__model', None)
        if benefit_plan_type__model:
            content_type = ContentType.objects.get(model=benefit_plan_type__model.lower())
            model_id = object_data.get('benefit_plan_id')
            try:
                content_type.get_object_for_this_type(pk=model_id)
            except Exception as e:
                raise AttributeError(e)
            object_data['benefit_plan_type'] = content_type
        obj = cls._model(**object_data)
        obj.save(username=user.username)
        return obj

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                ContributionPlanConfig.gql_mutation_create_paymentplan_perms):
            raise ValidationError(_("mutation.authentication_required"))
        if PaymentPlanService.check_unique_code(data['code']):
            raise ValidationError(_("mutation.payment_plan_code_duplicated"))
        validate_date_validity_range_on_create(cls._model, **data)

    class Input(PaymentPlanInputType):
        pass


class UpdatePaymentPlanMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "PaymentPlanMutation"
    _mutation_module = "contribution_plan"
    _model = PaymentPlan

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                ContributionPlanConfig.gql_mutation_update_paymentplan_perms):
            raise ValidationError(_("mutation.authentication_required"))

        if PaymentPlanService.check_unique_code(data['code'], data['id']):
            raise ValidationError(_("mutation.payment_plan_code_duplicated"))
        validate_date_validity_range_on_update(cls._model, **data)

    @classmethod
    def _mutate(cls, user, **data):
        if "date_valid_to" not in data:
            data['date_valid_to'] = None
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        updated_object = cls._model.objects.filter(id=data['id']).first()
        benefit_plan_type__model = data.pop('benefit_plan_type__model', None)
        if benefit_plan_type__model:
            model_id = data.get('benefit_plan_id')
            content_type = ContentType.objects.get(model=benefit_plan_type__model.lower())
            try:
                content_type.get_object_for_this_type(pk=model_id)
            except Exception as e:
                raise AttributeError(e)
            data['benefit_plan_type'] = content_type
        [setattr(updated_object, key, data[key]) for key in data]
        cls.update_object(user=user, object_to_update=updated_object)

    class Input(PaymentPlanUpdateInputType):
        pass


class DeletePaymentPlanMutation(BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "PaymentPlanMutation"
    _mutation_module = "contribution_plan"
    _model = PaymentPlan

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                ContributionPlanConfig.gql_mutation_delete_paymentplan_perms):
            raise ValidationError(_("mutation.authentication_required"))

    class Input(DeleteInputType):
        pass


class ReplacePaymentPlanMutation(BaseHistoryModelReplaceMutationMixin, BaseReplaceMutation):
    _mutation_class = "PaymentPlanMutation"
    _mutation_module = "contribution_plan"
    _model = PaymentPlan

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                ContributionPlanConfig.gql_mutation_replace_paymentplan_perms):
            raise ValidationError(_("mutation.authentication_required"))
        validate_date_validity_range(**data)

    class Input(PaymentPlanReplaceInputType):
        pass
