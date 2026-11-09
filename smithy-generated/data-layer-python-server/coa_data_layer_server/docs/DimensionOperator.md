# DimensionOperator

Comparison operator applied by a DimensionFilter.  Equality is the only supported comparison: Tier-1 binds the value as a bare SQL literal into a governed metric's template, which expresses `=` and nothing else. Declared as an enum rather than a free-form String so a client asking for an unsupported comparison is rejected by the contract instead of having it silently applied as equality — a wrong answer returned with a 200.

## Enum

* `EQUAL` (value: `'='`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


