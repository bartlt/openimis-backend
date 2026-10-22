from core.gql.gql_mutations.base_mutation import BaseMutation, BaseHistoryModelCreateMutationMixin
from policyholder.apps import PolicyholderConfig
from policyholder.services import PolicyHolder as PolicyHolderServices
from policyholder.models import PolicyHolder, PolicyHolderInsuree, PolicyHolderContributionPlan, PolicyHolderUser, \
    PolicyHolderMutation
from policyholder.gql.gql_mutations import PolicyHolderInputType, PolicyHolderInsureeInputType, \
    PolicyHolderContributionPlanInputType, PolicyHolderUserInputType
from policyholder.validation import PolicyHolderValidation
from policyholder.validation.permission_validation import PermissionValidation
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CreatePolicyHolderMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "PolicyHolderMutation"
    _mutation_module = "policyholder"
    _model = PolicyHolder

    class Input(PolicyHolderInputType):
        pass

    @classmethod
    def _mutate(cls, user, **data):
        client_mutation_id = data.pop('client_mutation_id', None)
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        policy_holder = cls.create_object(user=user, object_data=data)
        if client_mutation_id:
            PolicyHolderMutation.object_mutated(
                user, client_mutation_id=client_mutation_id, policy_holder=policy_holder
            )

    @classmethod
    def _validate_mutation(cls, user, **data):
        if PolicyHolderServices.check_unique_code_policy_holder(code=data['code']):
            raise ValidationError(_("mutation.ph_code_duplicated"))
        super()._validate_mutation(user, **data)
        PermissionValidation.validate_perms(user, PolicyholderConfig.gql_mutation_create_policyholder_perms)
        PolicyHolderValidation.validate_create(user, **data)


class CreatePolicyHolderInsureeMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "PolicyHolderInsureeMutation"
    _mutation_module = "policyholder"
    _model = PolicyHolderInsuree

    class Input(PolicyHolderInsureeInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        PermissionValidation.validate_perms(user, PolicyholderConfig.gql_mutation_create_policyholderinsuree_perms)


class CreatePolicyHolderContributionPlanMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "PolicyHolderContributionPlanMutation"
    _mutation_module = "policyholder"
    _model = PolicyHolderContributionPlan

    class Input(PolicyHolderContributionPlanInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        PermissionValidation.validate_perms(user, PolicyholderConfig.gql_mutation_create_policyholdercontributionplan_perms)


class CreatePolicyHolderUserMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "PolicyHolderUserMutation"
    _mutation_module = "policyholder"
    _model = PolicyHolderUser

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        cls.create_policy_holder_user(user=user, object_data=data)

    @classmethod
    def create_policy_holder_user(cls, user, object_data):
        obj = cls._model(**object_data)
        obj.save(user=user)
        return obj

    class Input(PolicyHolderUserInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        PermissionValidation.validate_perms(user, PolicyholderConfig.gql_mutation_create_policyholderuser_perms)
