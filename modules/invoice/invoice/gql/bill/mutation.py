import logging

import graphene
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from core.gql.gql_mutations.base_mutation import BaseMutation, BaseHistoryModelDeleteMutationMixin
from core.schema import OpenIMISMutation
from invoice.apps import InvoiceConfig
from invoice.models import Bill

logger = logging.getLogger(__name__)


class DeleteBillMutation(BaseHistoryModelDeleteMutationMixin, BaseMutation):
    _mutation_class = "DeleteBillMutation"
    _mutation_module = "invoice"
    _model = Bill

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                InvoiceConfig.gql_bill_delete_perms):
            raise ValidationError("mutation.authentication_required")

    class Input(OpenIMISMutation.Input):
        uuids = graphene.List(graphene.UUID)
