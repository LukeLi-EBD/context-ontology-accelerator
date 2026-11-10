# OntologyClassRef

One ontology class in the browse tree.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Class IRI. | 
**label** | **str** | Display label; the local name when the T-Box has no label. | 
**parents** | **List[str]** | Superclass IRIs; empty for a root class. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_class_ref import OntologyClassRef

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyClassRef from a JSON string
ontology_class_ref_instance = OntologyClassRef.from_json(json)
# print the JSON string representation of the object
print(OntologyClassRef.to_json())

# convert the object into a dict
ontology_class_ref_dict = ontology_class_ref_instance.to_dict()
# create an instance of OntologyClassRef from a dict
ontology_class_ref_from_dict = OntologyClassRef.from_dict(ontology_class_ref_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


