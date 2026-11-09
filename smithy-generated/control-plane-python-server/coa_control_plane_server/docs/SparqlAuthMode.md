# SparqlAuthMode

How the SPARQL client authenticates to the endpoint. SIGV4 is the only mode any v1 store uses (Neptune: the caller's IAM role is the identity, no secret). Secret- and token-based modes arrive with the first store that needs them.

## Enum

* `SIGV4` (value: `'sigv4'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


