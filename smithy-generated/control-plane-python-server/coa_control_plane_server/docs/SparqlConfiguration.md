# SparqlConfiguration

RDF/SPARQL graph source configuration — the RDF_SPARQL sub-type. Instance data (A-Box) lives natively as triples in a SPARQL store and is answered at serve time by NL→SPARQL executed directly against `dataEndpoint` (no Glue catalog, no VKG/SQL). There is no schema discovery: the ontology (T-Box) is imported separately and points its classes at this source by name.  Registration only verifies the endpoint is reachable (no scan). Persisted as the source `configuration` blob; serve and the verify Lambda both read it. Cross-field rules enforced server-side: `store = neptune` requires `authMode = sigv4` and forbids `credentialSecretArn`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**store** | [**SparqlStore**](SparqlStore.md) |  | [optional] 
**data_endpoint** | **str** | SPARQL endpoint for the A-Box (instance data) that serve executes against. | 
**region** | **str** | AWS region for SigV4 signing. Defaults to the deployment region. | [optional] 
**port** | **float** | Endpoint port. Defaults to 8182 (Neptune). | [optional] 
**data_named_graph** | **str** | Named graph holding the A-Box. When set, generated queries are confined to it; when absent, the store&#39;s default graph is queried. | [optional] 
**auth_mode** | [**SparqlAuthMode**](SparqlAuthMode.md) |  | [optional] 
**credential_secret_arn** | **str** | Credential for non-SigV4 auth modes. Rejected for &#x60;neptune&#x60;. | [optional] 

## Example

```python
from coa_control_plane_server.models.sparql_configuration import SparqlConfiguration

# TODO update the JSON string below
json = "{}"
# create an instance of SparqlConfiguration from a JSON string
sparql_configuration_instance = SparqlConfiguration.from_json(json)
# print the JSON string representation of the object
print(SparqlConfiguration.to_json())

# convert the object into a dict
sparql_configuration_dict = sparql_configuration_instance.to_dict()
# create an instance of SparqlConfiguration from a dict
sparql_configuration_from_dict = SparqlConfiguration.from_dict(sparql_configuration_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


