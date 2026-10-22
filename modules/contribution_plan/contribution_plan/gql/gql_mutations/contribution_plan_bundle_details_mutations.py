from contribution_plan.apps import ContributionPlanConfig
from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation  import BaseMutation, BaseDeleteMutation, BaseReplaceMutation, \
    BaseHistoryModelCreateMutationMixin, BaseHistoryModelUpdateMutationMixin, \
    BaseHistoryModelDeleteMutationMixin, BaseHistoryModelReplaceMutationMixin
from contribution_plan.gql.gql_mutations import ContributionPlanBundleDetailsInputType, \
    ContributionPlanBundleDetailsUpdateInputType, ContributionPlanBundleDetailsReplaceInputType
from contribution_plan.models import ContributionPlanBundleDetails
from django.utils.translation import gettext as _
from django.core.exceptions import PermissionDenied
from contribution_plan.gql.gql_mutations.validation import (
    validate_date_validity_range,
    validate_date_validity_range_on_create,
    validate_date_validity_range_on_update,
)


class CreateContributionPlanBundleDetailsMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "ContributionPlanBundleDetailsMutation"
    _mutation_module = "contribution_plan"
    _model = ContributionPlanBundleDetails

    class Input(ContributionPlanBundleDetailsInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(ContributionPlanConfig.gql_mutation_create_contributionplanbundle_perms):
            raise PermissionDenied(_("unauthorized"))
        validate_date_validity_range_on_create(cls._model, **data)



class UpdateContributionPlanBundleDetailsMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "ContributionPlanBundleDetailsMutation"
    _mutation_module = "contribution_plan"
    _model = ContributionPlanBundleDetails

    class Input(ContributionPlanBundleDetailsUpdateInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(ContributionPlanConfig.gql_mutation_update_contributionplanbundle_perms):
            raise PermissionDenied(_("unauthorized"))
        validate_date_validity_range_on_update(cls._model, **data)


class DeleteContributionPlanBundleDetailsMutation(BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "ContributionPlanBundleDetailsMutation"
    _mutation_module = "contribution_plan"
    _model = ContributionPlanBundleDetails

    class Input(DeleteInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(ContributionPlanConfig.gql_mutation_delete_contributionplanbundle_perms):
            raise PermissionDenied(_("unauthorized"))


class ReplaceContributionPlanBundleDetailsMutation(BaseHistoryModelReplaceMutationMixin, BaseReplaceMutation):
    _mutation_class = "ContributionPlanBundleDetailsMutation"
    _mutation_module = "contribution_plan"
    _model = ContributionPlanBundleDetails

    class Input(ContributionPlanBundleDetailsReplaceInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        if not user.has_perms(ContributionPlanConfig.gql_mutation_replace_contributionplanbundle_perms):
            raise PermissionDenied(_("unauthorized"))
        validate_date_validity_range(**data)
