from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation import BaseDeleteMutation, BaseHistoryModelDeleteMutationMixin
from policyholder.apps import PolicyholderConfig
from policyholder.models import PolicyHolder, PolicyHolderInsuree, PolicyHolderContributionPlan, PolicyHolderUser
from policyholder.validation.permission_validation import PermissionValidation


class DeletePolicyHolderMutation(BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "PolicyHolderMutation"
    _mutation_module = "policyholder"
    _model = PolicyHolder

    class Input(DeleteInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        PermissionValidation.validate_perms(user, PolicyholderConfig.gql_mutation_delete_policyholder_perms)


class DeletePolicyHolderInsureeMutation(BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "PolicyHolderInsureeMutation"
    _mutation_module = "policyholder"
    _model = PolicyHolderInsuree

    class Input(DeleteInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        PermissionValidation.validate_perms(user, PolicyholderConfig.gql_mutation_delete_policyholderinsuree_perms)


class DeletePolicyHolderContributionPlanMutation(BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "PolicyHolderContributionPlanMutation"
    _mutation_module = "policyholder"
    _model = PolicyHolderContributionPlan

    class Input(DeleteInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        PermissionValidation.validate_perms(user, PolicyholderConfig.gql_mutation_delete_policyholdercontributionplan_perms)


class DeletePolicyHolderUserMutation(BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "PolicyHolderUserMutation"
    _mutation_module = "policyholder"
    _model = PolicyHolderUser

    class Input(DeleteInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        PermissionValidation.validate_perms(user, PolicyholderConfig.gql_mutation_delete_policyholderuser_perms)
