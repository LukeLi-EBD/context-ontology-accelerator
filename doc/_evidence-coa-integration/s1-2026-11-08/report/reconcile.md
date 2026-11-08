# S1 指标校验对账（COA validator → JsonDataSourceLookup）

- OSI 文档解析：85/85 条，errors=0
- round-trip 语义一致：True
- 平台 manifest：total=85 publishable=60 executable=56 both=43
- COA SQL 通过：62；COA 整体 valid：62

| 分类 | 条数 |
| --- | --- |
| agree_executable | 56 |
| agree_not_executable | 23 |
| platform_not_executable_but_sql_present:no_observations | 5 |
| platform_not_executable_but_sql_present:quartet_incomplete | 1 |

## 差异逐条

| metric | executable | publishable | sqlSource | COA SQL | 原因 |
| --- | --- | --- | --- | --- | --- |
| FIN-BANK-035 | False | True | fact_function | True | 库内该口径无任何观测记录 |
| FIN-BANK-036-v1 | False | True | fact_function | True | 库内该口径无任何观测记录 |
| FIN-INS-004 | False | False | binding | True | 库内该口径无任何观测记录 |
| FIN-INS-017 | False | True | binding | True | 四元组不完整：缺 denominator_agg |
| FIN-INS-022-v2 | False | False | binding | True | 库内该口径无任何观测记录 |
| FIN-INS-023-v2 | False | False | binding | True | 库内该口径无任何观测记录 |

## 全量逐条（85 条）

| metric | publishable | executable | sqlSource | COA SQL | 分类 |
| --- | --- | --- | --- | --- | --- |
| CUST-001 | False | True | binding | True | agree_executable |
| CUST-002 | False | True | binding | True | agree_executable |
| CUST-003 | False | True | binding | True | agree_executable |
| CUST-004 | False | False | formula_text_fallback | False | agree_not_executable |
| CUST-005 | True | True | binding | True | agree_executable |
| CUST-006 | False | True | binding | True | agree_executable |
| CUST-007 | False | True | binding | True | agree_executable |
| CUST-008 | False | True | binding | True | agree_executable |
| CUST-009 | True | True | binding | True | agree_executable |
| CUST-010 | True | True | fact_function | True | agree_executable |
| CUST-011 | False | False | formula_text_fallback | False | agree_not_executable |
| CUST-012 | False | True | binding | True | agree_executable |
| CUST-013 | False | True | binding | True | agree_executable |
| FIN-BANK-001 | True | True | fact_function | True | agree_executable |
| FIN-BANK-002 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-003 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-004 | False | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-005 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-006 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-007 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-008 | True | True | binding | True | agree_executable |
| FIN-BANK-009 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-010 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-011 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-012 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-013 | True | True | binding | True | agree_executable |
| FIN-BANK-014 | True | True | binding | True | agree_executable |
| FIN-BANK-015 | True | True | binding | True | agree_executable |
| FIN-BANK-016 | True | True | binding | True | agree_executable |
| FIN-BANK-017 | True | True | binding | True | agree_executable |
| FIN-BANK-018 | True | True | binding | True | agree_executable |
| FIN-BANK-019 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-020 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-021 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-022 | True | True | binding | True | agree_executable |
| FIN-BANK-023 | True | True | binding | True | agree_executable |
| FIN-BANK-024 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-025 | True | True | binding | True | agree_executable |
| FIN-BANK-026 | True | True | binding | True | agree_executable |
| FIN-BANK-027 | True | True | binding | True | agree_executable |
| FIN-BANK-028 | True | True | binding | True | agree_executable |
| FIN-BANK-029 | True | True | binding | True | agree_executable |
| FIN-BANK-030 | True | True | binding | True | agree_executable |
| FIN-BANK-031 | True | True | fact_function | True | agree_executable |
| FIN-BANK-032 | True | True | fact_function | True | agree_executable |
| FIN-BANK-033 | True | True | binding | True | agree_executable |
| FIN-BANK-034 | False | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-035 | True | False | fact_function | True | platform_not_executable_but_sql_present:no_observations |
| FIN-BANK-036 | False | False | formula_text_fallback | False | agree_not_executable |
| FIN-BANK-036-v1 | True | False | fact_function | True | platform_not_executable_but_sql_present:no_observations |
| FIN-BANK-036-v2 | False | True | fact_function | True | agree_executable |
| FIN-INS-001 | False | True | fact_function | True | agree_executable |
| FIN-INS-002 | True | True | binding | True | agree_executable |
| FIN-INS-003 | True | True | binding | True | agree_executable |
| FIN-INS-004 | False | False | binding | True | platform_not_executable_but_sql_present:no_observations |
| FIN-INS-005 | False | True | binding | True | agree_executable |
| FIN-INS-006 | True | True | binding | True | agree_executable |
| FIN-INS-007 | True | True | binding | True | agree_executable |
| FIN-INS-008 | True | True | binding | True | agree_executable |
| FIN-INS-009 | False | True | binding | True | agree_executable |
| FIN-INS-010 | False | True | binding | True | agree_executable |
| FIN-INS-011 | True | True | binding | True | agree_executable |
| FIN-INS-012 | True | False | formula_text_fallback | False | agree_not_executable |
| FIN-INS-013 | True | True | binding | True | agree_executable |
| FIN-INS-014 | True | True | binding | True | agree_executable |
| FIN-INS-015 | True | True | binding | True | agree_executable |
| FIN-INS-016 | True | True | binding | True | agree_executable |
| FIN-INS-017 | True | False | binding | True | platform_not_executable_but_sql_present:quartet_incomplete |
| FIN-INS-018 | True | True | binding | True | agree_executable |
| FIN-INS-019 | True | True | binding | True | agree_executable |
| FIN-INS-020 | True | True | binding | True | agree_executable |
| FIN-INS-021 | True | True | fact_function | True | agree_executable |
| FIN-INS-022 | False | False | formula_text_fallback | False | agree_not_executable |
| FIN-INS-022-v1 | True | True | binding | True | agree_executable |
| FIN-INS-022-v2 | False | False | binding | True | platform_not_executable_but_sql_present:no_observations |
| FIN-INS-023 | False | False | formula_text_fallback | False | agree_not_executable |
| FIN-INS-023-v1 | True | True | binding | True | agree_executable |
| FIN-INS-023-v2 | False | False | binding | True | platform_not_executable_but_sql_present:no_observations |
| FIN-INS-024 | True | True | binding | True | agree_executable |
| FIN-INS-025 | True | True | fact_function | True | agree_executable |
| FIN-INS-026 | True | True | binding | True | agree_executable |
| FIN-INS-027 | True | True | binding | True | agree_executable |
| FIN-INS-028 | True | True | binding | True | agree_executable |
| FIN-INS-029 | False | False | formula_text_fallback | False | agree_not_executable |
| FIN-INS-030 | False | False | formula_text_fallback | False | agree_not_executable |
