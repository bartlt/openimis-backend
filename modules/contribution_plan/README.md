# openIMIS Backend Contribution Plan reference module
This repository holds the files of the openIMIS Backend ContributionPlan and ContributionPlanBundle reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

## ORM mapping:
* tblContributionPlanBundle > ContributionPlanBundle
* tblContributionPlan > ContributionPlan
* tblContributionPlanBundleDetails > ContributionPlanBundleDetails

## GraphQl Queries
* contributionPlanBundle 
* contributionPlan
* contributionPlanBundleDetails

## GraphQL Mutations - each mutation emits default signals and return standard error lists (cfr. openimis-be-core_py)
* createContributionPlanBundle
* updateContributionPlanBundle
* deleteContributionPlanBundle
* replaceContributionPlanBundle
* createContributionPlan
* updateContributionPlan
* deleteContributionPlan
* replaceContributionPlan
* createContributionPlanBundleDetails
* updateContributionPlanBundleDetails
* deleteContributionPlanBundleDetails

## Services
* ContributionPlanBundle - CRUD services, replace
* ContributionPlan - CRUD services, replace
* ContributionPlanBundleDetails - create, update, delete

## Configuration options (can be changed via core.ModuleConfiguration)
* gql_query_contributionplanbundle_perms: required rights to call contribution_plan_bundle GraphQL Query (default: ["151101"])
* gql_query_contributionplanbundle_admins_perms: required rights to call contribution_plan_bundle_admin GraphQL Query (default: [])

* gql_query_contributionplan_perms: required rights to call contribution_plan GraphQL Query (default: ["151201"])
* gql_query_contributionplan_admins_perms: required rights to call contribution_plan_admin GraphQL Query (default: [])

* gql_mutation_create_contributionplanbundle_perms: required rights to call createContributionPlanBundle GraphQL Mutation (default: ["151102"])
* gql_mutation_update_contributionplanbundle_perms: required rights to call updateContributionPlanBundle GraphQL Mutation (default: ["151103"])
* gql_mutation_delete_contributionplanbundle_perms: required rights to call deleteContributionPlanBundle GraphQL Mutation (default: ["151104"])
* gql_mutation_replace_contributionplanbundle_perms: required rights to call replaceContributionPlanBundle GraphQL Mutation (default: ["151106"])

* gql_mutation_create_contributionplan_perms: required rights to call createContributionPlan GraphQL Mutation (default: ["151202"])
* gql_mutation_update_contributionplan_perms: required rights to call updateContributionPlan GraphQL Mutation (default: ["151203"])
* gql_mutation_delete_contributionplan_perms: required rights to call deleteContributionPlan GraphQL Mutation (default: ["151204"])
* gql_mutation_replace_contributionplan_perms: required rights to call replaceContributionPlan GraphQL Mutation (default: ["151206"])