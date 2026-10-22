import graphene
import graphene_django_optimizer as gql_optimizer

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q

from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from invoice.apps import InvoiceConfig
from invoice.gql.gql_types.payment_types import DetailPaymentInvoiceGQLType
from invoice.models import DetailPaymentInvoice


class DetailPaymentInvoiceQueryMixin:
    detail_payment_invoice = OrderedDjangoFilterConnectionField(
        DetailPaymentInvoiceGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
    )

    def resolve_detail_payment_invoice(self, info, **kwargs):
        filters = []
        filters += append_validity_filter(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        DetailPaymentInvoiceQueryMixin._check_permissions(info.context.user)
        return gql_optimizer.query(DetailPaymentInvoice.objects.filter(*filters).all(), info)

    @staticmethod
    def _check_permissions(user):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                InvoiceConfig.gql_invoice_payment_search_perms):
            raise PermissionError("Unauthorized")
