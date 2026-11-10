# OntologyClassInstance

A class whose instances would disappear.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_class** | **str** | Class IRI. | 
**instances** | **float** | Current instance count of that class. | 

## Example

```python
from coa_control_plane_server.models.ontology_class_instance import OntologyClassInstance

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyClassInstance from a JSON string
ontology_class_instance_instance = OntologyClassInstance.from_json(json)
# print the JSON string representation of the object
print(OntologyClassInstance.to_json())

# convert the object into a dict
ontology_class_instance_dict = ontology_class_instance_instance.to_dict()
# create an instance of OntologyClassInstance from a dict
ontology_class_instance_from_dict = OntologyClassInstance.from_dict(ontology_class_instance_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


