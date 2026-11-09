# SparqlStore

SPARQL engine behind an RDF_SPARQL source — a dialect one level below the sub-type, the way DatabaseEngine sits below JDBC_DATABASE. It selects the serve-time client and the registration-time reachability probe; adding an engine adds a member here plus one client and one probe, never a new sub-type. Values are lowercase because they are persisted verbatim in the source `configuration` blob.

## Enum

* `NEPTUNE` (value: `'neptune'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


