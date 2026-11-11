# OntologyImpactError

Why the impact analysis could not be produced.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **str** | Stable provider code. | 
**message** | **str** | Human-readable explanation. | 
**details** | **object** | Code-specific detail, e.g. the version that could not be read. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact_error import OntologyImpactError

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactError from a JSON string
ontology_impact_error_instance = OntologyImpactError.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactError.to_json())

# convert the object into a dict
ontology_impact_error_dict = ontology_impact_error_instance.to_dict()
# create an instance of OntologyImpactError from a dict
ontology_impact_error_from_dict = OntologyImpactError.from_dict(ontology_impact_error_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


