# openimis-be-calculation-rule-fs_salary_procentage_py
This repository holds the files of the openIMIS Backend calculation rule fs income percentage reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py). It is an 
extended part of calculation module [openimis-be-calculation_py](https://github.com/openimis/openimis-be-calculation_py) 
and therefore that module is dependent on this core calculation module. This module contains additional calculation rules. 

## Models
  - None (using no database approach for CalculationRule) - Calculation Rule is saved by defining class 
    extending the ABSCalculationClass from core module.


## GraphQl Queries
  None

## Services
  None

## Configuration options (can be changed via core.ModuleConfiguration)
  loading implemented rules from "calculation_rule.py" into global variable "CALCULATION_RULE"
