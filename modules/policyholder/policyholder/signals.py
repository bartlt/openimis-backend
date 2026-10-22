from django.db.models import Q
from payment.apps import PaymentConfig
from .apps import PolicyholderConfig
from .models import PolicyHolderUser


def append_policy_holder_filter(sender, **kwargs):
    # OFS-257: Create dynamic filters for the payment mutation
    user = kwargs.get("user", None)
    additional_filter = kwargs.get('additional_filter', None)
    if "policyHolder" in additional_filter:
        # then check perms
        if user.has_perms(PaymentConfig.gql_query_payments_perms) or user.has_perms(PolicyholderConfig.gql_query_payment_portal_perms):
            ph_id = additional_filter["policyHolder"]
            # check if user is linked to ph in policy holder user table
            type_user = f"{user}"
            # related to user object output (i) or (t)
            # check if we have interactive user from current context
            if '(i)' in type_user:
                from core import datetime
                now = datetime.datetime.now()
                ph_user = PolicyHolderUser.objects.filter(
                    Q(date_valid_to__isnull=True) | Q(date_valid_to__gte=now),
                    date_valid_from__lte=now,
                    policy_holder__id=ph_id,
                    user__id=user.id
                ).first()
                if ph_user or user.has_perms(PaymentConfig.gql_query_payments_perms):
                    return Q(
                        payment_details__premium__contract_contribution_plan_details__contract_details__contract__policy_holder__id=ph_id
                    )
