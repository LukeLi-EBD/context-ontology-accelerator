# OntologyInstanceRef

One instance of a class.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Instance IRI. | 
**label** | **str** | Display label; the local name when the instance has no label. | 
**graph** | **str** | Graph the instance was found in. | 

## Example

```python
from coa_control_plane_server.models.ontology_instance_ref import OntologyInstanceRef

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyInstanceRef from a JSON string
ontology_instance_ref_instance = OntologyInstanceRef.from_json(json)
# print the JSON string representation of the object
print(OntologyInstanceRef.to_json())

# convert the object into a dict
ontology_instance_ref_dict = ontology_instance_ref_instance.to_dict()
# create an instance of OntologyInstanceRef from a dict
ontology_instance_ref_from_dict = OntologyInstanceRef.from_dict(ontology_instance_ref_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


