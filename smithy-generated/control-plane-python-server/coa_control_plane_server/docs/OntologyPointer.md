# OntologyPointer

The `tbox/current` pointer row.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Pointer name, always &#x60;tbox/current&#x60; in this deployment. | [optional] 
**version_id** | **str** | Version the pointer currently selects. | 
**semver** | **str** | Semver of the selected version. | [optional] 
**content_hash** | **str** | Canonical hash of the selected version. | [optional] 
**graph** | **str** | Graph IRI of the selected version. | [optional] 
**updated_at** | **str** | Last pointer move (ISO-8601). | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_pointer import OntologyPointer

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyPointer from a JSON string
ontology_pointer_instance = OntologyPointer.from_json(json)
# print the JSON string representation of the object
print(OntologyPointer.to_json())

# convert the object into a dict
ontology_pointer_dict = ontology_pointer_instance.to_dict()
# create an instance of OntologyPointer from a dict
ontology_pointer_from_dict = OntologyPointer.from_dict(ontology_pointer_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


