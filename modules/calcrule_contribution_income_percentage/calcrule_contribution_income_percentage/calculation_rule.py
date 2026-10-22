import json

from core.abs_calculation_rule  import AbsStrategy
from .config import CLASS_RULE_PARAM_VALIDATION, \
    DESCRIPTION_CONTRIBUTION_VALUATION, FROM_TO
from contribution_plan.models import ContributionPlanBundleDetails
from core.signals import Signal
from core import datetime
from django.contrib.contenttypes.models import ContentType
from policyholder.models import PolicyHolderInsuree
from uuid import UUID

class ContributionValuationRule(AbsStrategy):
    version = 1
    uuid = "0e1b6dd4-04a0-4ee6-ac47-2a99cfa5e9a8"
    calculation_rule_name = "CV: percent of income"
    description = DESCRIPTION_CONTRIBUTION_VALUATION
    impacted_class_parameter = CLASS_RULE_PARAM_VALIDATION
    date_valid_from = datetime.datetime(2000, 1, 1)
    date_valid_to = None
    status = "active"
    from_to = FROM_TO
    type = "account_receivable"
    sub_type = "contribution"



    @classmethod
    def active_for_object(cls, instance, context, type='account_receivable', sub_type='contribution'):
        return (
            instance.__class__.__name__ == "ContractContributionPlanDetails"
            and context in ["value", "members", "validity"]
        ) and cls.check_calculation(instance)

    @classmethod
    def check_calculation(cls, instance):
        match = False
        class_name = instance.__class__.__name__
        list_class_name = [
            "PolicyHolder", "ContributionPlan",
            "PolicyHolderInsuree", "ContractDetails",
            "ContractContributionPlanDetails", "ContributionPlanBundle"
        ]
        if class_name == "ABCMeta":
            match = UUID(str(cls.uuid)) == UUID(str(instance.uuid))
        elif class_name == "ContributionPlan":
            match = UUID(str(cls.uuid)) == UUID(str(instance.calculation))
        elif class_name == "ContributionPlanBundle":
            list_cpbd = list(instance.contributionplanbundledetails_set.filter(
                is_deleted=False
            ))
            for cpbd in list_cpbd:
                if match is False:
                    if cls.check_calculation(cpbd.contribution_plan):
                        match = True
        else:
            related_fields = [
                f.name for f in instance.__class__._meta.fields
                if f.get_internal_type() == 'ForeignKey' and f.remote_field.model.__name__ in list_class_name
            ]
            for rf in related_fields:
                match = cls.check_calculation(getattr(instance, rf))
        return match

    @classmethod
    def calculate(cls, instance, **kwargs):
        context = kwargs.get('context', None)
        if instance.__class__.__name__ == "ContractContributionPlanDetails":
            if context == 'value':
                # check type of json_ext - in case of string - json.loads
                cp_params, cd_params = instance.contribution_plan.json_ext, instance.contract_details.json_ext
                ph_insuree = PolicyHolderInsuree.objects.filter(
                    insuree=instance.contract_details.insuree).first()
                phi_params = ph_insuree.json_ext
                if isinstance(cp_params, str):
                    cp_params = json.loads(cp_params)
                if isinstance(cd_params, str):
                    cd_params = json.loads(cd_params)
                if isinstance(phi_params, str):
                    phi_params = json.loads(phi_params)
                # check if json external calculation rule in instance exists
                if cp_params:
                    cp_params = cp_params["calculation_rule"] if "calculation_rule" in cp_params else None
                if cd_params:
                    cd_params = cd_params["calculation_rule"] if "calculation_rule" in cd_params else None
                if phi_params:
                    phi_params = phi_params["calculation_rule"] if "calculation_rule" in phi_params else None
                if cp_params is not None and "rate" in cp_params:
                    rate = int(cp_params["rate"])
                    if cd_params:
                        if "income" in cd_params:
                            income = float(cd_params["income"])
                        elif "income" in phi_params:
                            income = float(phi_params["income"])
                        else:
                            return False
                    elif "income" in phi_params:
                        income = float(phi_params["income"])
                    else:
                        return False
                    value = float(income) * (rate / 100)
                    return value
            elif context == 'members':
                cp_params, cd_params = instance.contribution_plan.json_ext, instance.contract_details.json_ext
                if (
                    instance.contract_details.insuree.family
                    and 'calculation_rule' in cp_params
                    and 'includeFamily' in cp_params['calculation_rule']
                    and cp_params['calculation_rule']['includeFamily']
                ):
                    return list(instance.contract_details.insuree.family.members.filter(
                        validity_to__isnull=True
                    ))
                else:
                    return [instance.contract_details.insuree]

            elif context == 'validity':
                validity_from = kwargs.get('validity_from', None)
                validity_to = kwargs.get('validity_to', None)
                contract = None
                if instance.__class__.__name__ == "Contract":
                    contract = instance
                elif instance.__class__.__name__ == "ContractContributionPlanDetails":
                    contract = instance.contract_details.contract
                if instance.__class__.__name__ == "ContractDetails":
                    contract = instance.contract

                
                if contract:
                    validity_from = validity_from or contract.date_valid_from
                    validity_to = validity_to or contract.date_valid_to
                    date_approved = contract.date_approved or validity_from
                else:
                    date_approved = validity_from
                if validity_from and validity_to:
                    return {
                        'enroll_date': date_approved,
                        'start_date': validity_from,
                        'effective_date': validity_from,
                        'expiry_date': validity_to
                    }

    @classmethod
    def get_linked_class(cls, sender, class_name, **kwargs):
        list_class = super().get_linked_class(sender, class_name, **kwargs)

        # because we have calculation in ContributionPlan
        #  as uuid - we have to consider this case
        if class_name == "ContributionPlan":
            list_class.append("Calculation")
        # because we have no direct relation in ContributionPlanBundle
        #  to ContributionPlan we have to consider this case
        if class_name == "ContributionPlanBundle":
            list_class.append("ContributionPlan")
        return list_class
