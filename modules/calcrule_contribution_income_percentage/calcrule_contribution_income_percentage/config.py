CLASS_RULE_PARAM_VALIDATION = [
    {
        "class": "ContributionPlan",
        "parameters": [
            {
                "type": "select",
                "name": "rate",
                "label": {
                    "en": "Percentage of income",
                    "fr": "Pourcentage du salaire"
                },
                "rights": {
                    "read": "151201",
                    "write": "151202",
                    "update": "151203",
                    "replace": "151206",
                },
                'relevance': "True",
                'condition': "INPUT>1",
                'optionSet': [
                    {
                        "value": "5",
                        "label": {
                            "en": "5%",
                            "fr": "5%"
                        }
                    },
                    {
                        "value": "10",
                        "label": {
                            "en": "10%",
                            "fr": "10%"
                        }
                    },
                    {
                        "value": "15",
                        "label": {
                            "en": "15%",
                            "fr": "15%"
                        }
                    },
                ],
                "default": "5"
            },
            {
                "type": "checkbox",
                "name": "includeFamily",
                "label": {
                    "en": "include family members",
                    "fr": "Inclure les membres de la familles"
                },
                "rights": {
                    "read": "151201",
                    "write": "151202",
                    "update": "151203",
                    "replace": "151206",
                },
                "relevance": "True",
                "default": "False"
            },
        ],
    },
    {
        "class": "ContractDetails",
        "parameters": [
            {
                "type": "number",
                "name": "income",
                "label": {
                    "en": "Income",
                    "fr": "Salaire"
                },
                "rights": {
                    "read": ["152101","154201"],
                    "write": ["152102","154202"],
                    "update": ["152103","154203"],
                    "replace": ["152103","154203"],
                },
                "relevance": "True",
                "condition": "INPUT>100",
                "default": ""
            }
        ],
    },
    {
        "class": "PolicyHolderInsuree",
        "parameters": [
            {
                "type": "number",
                "name": "income",
                "label": {
                    "en": "Income",
                    "fr": "Salaire"
                },
                "rights": {
                    "read": ["150201","154101"],
                    "write": ["150202","154102"],
                    "update": ["150203","154103"],
                    "replace": ["150203","154103"],
                },
                "relevance": "True",
                "condition": "INPUT>100",
                "default": ""
            }
        ],
    },
]

DESCRIPTION_CONTRIBUTION_VALUATION = F"" \
    F"This calcutation will add the income in the contract details " \
    F"and PHinsuree and the percentage in the Contribution plan" \
    F" so when a contract valuation is requested then the calculation will" \
    F" determine the value based on the contract details income and CP percentage"

FROM_TO = []
