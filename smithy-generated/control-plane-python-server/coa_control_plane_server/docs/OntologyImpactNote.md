# OntologyImpactNote

A registry that could not be read while computing the dependencies.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source** | **str** | Registry name, e.g. &#x60;metric_definition&#x60;. | 
**error** | **str** | Provider error raised while reading that registry. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_note import OntologyImpactNote

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactNote from a JSON string
ontology_impact_note_instance = OntologyImpactNote.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactNote.to_json())

# convert the object into a dict
ontology_impact_note_dict = ontology_impact_note_instance.to_dict()
# create an instance of OntologyImpactNote from a dict
ontology_impact_note_from_dict = OntologyImpactNote.from_dict(ontology_impact_note_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


