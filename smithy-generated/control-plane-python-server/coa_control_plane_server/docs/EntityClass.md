# EntityClass

One class asserted or inferred for the entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Class IRI. | 
**label** | **str** | Class label. | 
**labeled** | **bool** | True when the class has a label in the T-Box. | 
**inferred_only** | **bool** | True when the membership exists only in the inferred graph. | 
**instance_count** | **float** | Number of instances of this class. | 
**chain** | [**List[EntityClassLink]**](EntityClassLink.md) | Superclass chain, nearest first. | 

## Example

```python
from coa_control_plane_server.models.entity_class import EntityClass

# TODO update the JSON string below
json = "{}"
# create an instance of EntityClass from a JSON string
entity_class_instance = EntityClass.from_json(json)
# print the JSON string representation of the object
print(EntityClass.to_json())

# convert the object into a dict
entity_class_dict = entity_class_instance.to_dict()
# create an instance of EntityClass from a dict
entity_class_from_dict = EntityClass.from_dict(entity_class_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


