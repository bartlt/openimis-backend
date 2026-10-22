# openIMIS Backend PolicyHolder reference module
This repository holds the files of the openIMIS Backend PolicyHolder reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

## ORM mapping:
* tblPolicyHolder  > PolicyHolder 
* tblPolicyHolderInsuree > PolicyHolderInsuree
* tblPolicyHolderContributionPlanBundle  > PolicyHolderContributionPlanBundle
* tblPolicyHolderUser > PolicyHolderUser

## GraphQL Queries
* policyHolder
* PolicyHolderInsuree
* PolicyHolderContributionPlanBundle
* PolicyHolderUser

## GraphQL Mutations - each mutation emits default signals and return standard error lists (cfr. openimis-be-core_py)
* createPolicyHolder
* updatePolicyHolder
* deletePolicyHolder
* createPolicyHolderInsuree
* updatePolicyHolderInsuree
* deletePolicyHolderInsuree
* replacePolicyHolderInsuree
* createPolicyHolderContributionPlanBundle
* updatePolicyHolderContributionPlanBundle
* deletePolicyHolderContributionPlanBundle
* replacePolicyHolderContributionPlanBundle
* createPolicyHolderUser
* updatePolicyHolderUser
* deletePolicyHolderUser
* replacePolicyHolderUser

## Services
* PolicyHolder - CRUD services 
* PolicyHolderInsuree - CRUD services, replacePolicyHolderInsuree
* PolicyHolderContributionPlanBundle - CRUD services, replacePoicyHolderContributionPlanBundle
* PolicyHolderUser - CRUD services, replacePolicyHolderUser

## Configuration options (can be changed via core.ModuleConfiguration)
* gql_query_policyholder_perms: required rights to call policy_holder GraphQL Query (default: ["150101"])
* gql_query_policyholder_admins_perms: required rights to call policy_holder_admin GraphQL Query (default: [])
* gql_query_policyholderinsuree_perms: required rights to call policy_holder_insuree GraphQL Query (default: ["150201"])
* gql_query_policyholderinsuree_admins_perms: required rights to call policy_holder_insuree_admin GraphQL Query (default: [])
* gql_query_policyholderuser_perms: required rights to call policy_holder_user GraphQL Query (default: ["150301"])
* gql_query_policyholderuser_admins_perms: required rights to call policy_holder_user_admin GraphQL Query (default: [])
* gql_query_policyholdercontributionplanbundle_perms: required rights to call policy_holder_contribution_plan_bundle GraphQL Query (default: ["150401"])
* gql_query_policyholdercontributionplanbundle_admins_perms: required rights to call policy_holder_contribution_plan_bundle_admin GraphQL Query (default: [])

* gql_mutation_create_policyholder_perms: required rights to call createPolicyHolder GraphQL Mutation (default: ["150102"])
* gql_mutation_update_policyholder_perms: required rights to call updatePolicyHolder GraphQL Mutation (default: ["150103"])
* gql_mutation_delete_policyholder_perms: required rights to call deletePolicyHolder GraphQL Mutation (default: ["150104"])
   
* gql_mutation_create_policyholderinsuree_perms: required rights to call createPolicyHolderInsuree GraphQL Mutation (default: ["150202"]),
* gql_mutation_update_policyholderinsuree_perms: required rights to call updatePolicyHolderInsuree GraphQL Mutation (default: ["150203"]),
* gql_mutation_delete_policyholderinsuree_perms: required rights to call deletePolicyHolderInsuree GraphQL Mutation (default: ["150204"]),
* gql_mutation_replace_policyholderinsuree_perms: required rights to call replacePolicyHolderInsuree GraphQL Mutation (default: ["150206"]),
    
* gql_mutation_create_policyholderuser_perms: required rights to call createPolicyHolderUser GraphQL Mutation (default: ["150302"]),
* gql_mutation_update_policyholderuser_perms: required rights to call updatePolicyHolderUser GraphQL Mutation (default: ["150303"]),
* gql_mutation_delete_policyholderuser_perms: required rights to call deletePolicyHolderUser GraphQL Mutation (default: ["150304"]),
* gql_mutation_replace_policyholderuser_perms: required rights to call replacePolicyHolderUser GraphQL Mutation (default: ["150306"]),
    
* gql_mutation_create_policyholdercontributionplan_perms: required rights to call createPolicyHolderContributionPlanBundle GraphQL Mutation (default: ["150402"]),
* gql_mutation_update_policyholdercontributionplan_perms: required rights to call updatePolicyHolderContributionPlanBundle GraphQL Mutation (default: ["150403"]),
* gql_mutation_delete_policyholdercontributionplan_perms: required rights to call deletePolicyHolderContributionPlanBundle GraphQL Mutation (default: ["150404"]),
* gql_mutation_replace_policyholdercontributionplan_perms: required rights to call replacePolicyHolderContributionPlanBundle GraphQL Mutation (default: ["150406"]),

## openIMIS Modules Dependencies
- core.models.HistoryBusinessModel
- contribution_plan.models.ContributionPlanBundle
- insuree.models.Insuree
- location.models.Location
- policy.models.Policy
- payment.models.Payment