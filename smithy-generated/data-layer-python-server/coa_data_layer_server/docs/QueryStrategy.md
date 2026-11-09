# QueryStrategy

Which Tier-2 engine answers a structured query. Absent = the serve default (``nl_to_sql_first``).  This is a DIFFERENT axis from ``mode``: ``mode`` chooses whether the whole T1→T2→T3 cascade is replaced by the Tier-3 reasoning loop, while ``strategy`` chooses which engine answers within Tier 2. Both were called \"agentic\" before the rebrand, which is why the distinction is spelled out here.  An explicit value is caller intent and is never overridden by automatic tier gating or per-query Tier-2 pruning.

## Enum

* `BEST` (value: `'best'`)

* `ONTOP` (value: `'ontop'`)

* `NL_TO_SQL` (value: `'nl_to_sql'`)

* `ONTOP_FIRST` (value: `'ontop_first'`)

* `NL_TO_SQL_FIRST` (value: `'nl_to_sql_first'`)

* `DEEP_MINUS_REASONING` (value: `'deep-reasoning'`)

* `NL_TO_SPARQL` (value: `'nl_to_sparql'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


