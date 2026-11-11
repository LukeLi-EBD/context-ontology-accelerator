# GetOntologyVersionResponseContent

A version row plus its proposals and audit events.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Version identifier. | 
**version_id** | **str** | Contract alias of &#x60;id&#x60;. | 
**semver** | **str** | Semantic version. | 
**status** | [**OntologyVersionStatus**](OntologyVersionStatus.md) |  | 
**content_hash** | **str** | SHA-256 of the canonical graph. | [optional] 
**triple_count** | **float** | Declared triple count. | [optional] 
**format** | **str** | Source serialisation. | [optional] 
**graph** | **str** | Graph IRI holding the triples. | [optional] 
**graph_uri** | **str** | Contract alias of &#x60;graph&#x60;. | [optional] 
**statement_count** | **float** | Contract alias of &#x60;tripleCount&#x60;. | [optional] 
**graph_triple_count** | **float** | Triples actually present in the graph store. | [optional] 
**rollback_of** | **str** | Version this one rolled back to, when applicable. | [optional] 
**label** | **str** | Human-readable label. | [optional] 
**created_at** | **str** | Creation time (ISO-8601). | [optional] 
**published_at** | **str** | Publish time (ISO-8601). | [optional] 
**proposals** | [**List[OntologyProposal]**](OntologyProposal.md) | Proposals filed against this version. | [optional] 
**events** | [**List[OntologyEvent]**](OntologyEvent.md) | Audit events recorded for this version. | [optional] 

## Example

```python
from coa_control_plane_server.models.get_ontology_version_response_content import GetOntologyVersionResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOntologyVersionResponseContent from a JSON string
get_ontology_version_response_content_instance = GetOntologyVersionResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetOntologyVersionResponseContent.to_json())

# convert the object into a dict
get_ontology_version_response_content_dict = get_ontology_version_response_content_instance.to_dict()
# create an instance of GetOntologyVersionResponseContent from a dict
get_ontology_version_response_content_from_dict = GetOntologyVersionResponseContent.from_dict(get_ontology_version_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


