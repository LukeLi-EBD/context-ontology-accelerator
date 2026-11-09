# GlueExecutionEngine

Execution engine choice for a Glue/Iceberg source. A deliberately narrow enum (only the engines valid for a Glue source) so the onboarding UI/API cannot select an engine — e.g. direct JDBC — that doesn't apply to Glue.

## Enum

* `ATHENA` (value: `'ATHENA'`)

* `REDSHIFT` (value: `'REDSHIFT'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


