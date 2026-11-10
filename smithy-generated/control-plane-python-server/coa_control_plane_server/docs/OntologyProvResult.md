# OntologyProvResult

PROV chain verification result.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ok** | **bool** | True when every PROV link verifies. | 
**checked** | **float** | Number of PROV events checked. | 
**error** | **str** | First failure, when &#x60;ok&#x60; is false. | [optional] 
**last_hash** | **str** | Hash of the last verified event. | [optional] 
**graph** | **str** | PROV graph IRI. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_prov_result import OntologyProvResult

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyProvResult from a JSON string
ontology_prov_result_instance = OntologyProvResult.from_json(json)
# print the JSON string representation of the object
print(OntologyProvResult.to_json())

# convert the object into a dict
ontology_prov_result_dict = ontology_prov_result_instance.to_dict()
# create an instance of OntologyProvResult from a dict
ontology_prov_result_from_dict = OntologyProvResult.from_dict(ontology_prov_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


