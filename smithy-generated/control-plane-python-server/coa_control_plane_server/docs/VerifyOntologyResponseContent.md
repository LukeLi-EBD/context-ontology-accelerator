# VerifyOntologyResponseContent

Result of `VerifyOntology`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ok** | **bool** | True when every link in the lifecycle chain verifies. | 
**checked** | **float** | Number of events checked before the first failure or the end. | 
**error** | **str** | First failure, when &#x60;ok&#x60; is false. | [optional] 
**prov** | [**OntologyProvResult**](OntologyProvResult.md) |  | 
**separation** | [**OntologySeparationResult**](OntologySeparationResult.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.verify_ontology_response_content import VerifyOntologyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of VerifyOntologyResponseContent from a JSON string
verify_ontology_response_content_instance = VerifyOntologyResponseContent.from_json(json)
# print the JSON string representation of the object
print(VerifyOntologyResponseContent.to_json())

# convert the object into a dict
verify_ontology_response_content_dict = verify_ontology_response_content_instance.to_dict()
# create an instance of VerifyOntologyResponseContent from a dict
verify_ontology_response_content_from_dict = VerifyOntologyResponseContent.from_dict(verify_ontology_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


