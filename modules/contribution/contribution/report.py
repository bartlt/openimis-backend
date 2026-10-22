from contribution.reports import premium_collection, payment_category_overview, contributions_distribution
from contribution.reports.contributions_distribution import contributions_distribution_query
from contribution.reports.payment_category_overview import payment_category_overview_query
from contribution.reports.premium_collection import premium_collection_query

report_definitions = [
    {
        "name": "premium_collection",
        "engine": 0,
        "default_report": premium_collection.template,
        "description": "Premium collection",
        "module": "contribution",
        "python_query": premium_collection_query,
        "permission": ["131204"],
    },
    {
        "name": "payment_category_overview",
        "engine": 0,
        "default_report": payment_category_overview.template,
        "description": "Payment category overview",
        "module": "contribution",
        "python_query": payment_category_overview_query,
        "permission": ["131211"],
    },
    {
        "name": "contributions_distribution",
        "engine": 0,
        "default_report": contributions_distribution.template,
        "description": "Contributions distribution",
        "module": "contribution",
        "python_query": contributions_distribution_query,
        "permission": ["131206"],
    },
]
