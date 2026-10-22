import json

from contribution_plan.models import GenericPlan


def obtain_calcrule_params(plan: GenericPlan,
    integer_param_list: list, none_integer_param_list: list) -> dict:
    # obtaining payment plan params saved in payment plan json_ext fields
    pp_params = plan.json_ext
    if isinstance(pp_params, str):
        pp_params = json.loads(pp_params)
    if pp_params:
        pp_params = pp_params["calculation_rule"] if "calculation_rule" in pp_params else None

    # correct empty string values
    for key in integer_param_list:
        if key in pp_params.keys():
            value = pp_params[f'{key}']
            if value == "":
                pp_params[f'{key}'] = 0
            else:
                pp_params[f'{key}'] = int(value)
        else:
            pp_params[f'{key}'] = 0

    for key in none_integer_param_list:
        if key not in pp_params.keys():
            pp_params[f'{key}'] = None
        else:
            value = pp_params[f'{key}']
            if value == "null":
                pp_params[f'{key}'] = None
    return pp_params
