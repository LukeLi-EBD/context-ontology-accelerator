# EntityProperty

One property and its values on the entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_property** | **str** | Property IRI. | 
**label** | **str** | Property label. | 
**values** | [**List[EntityTerm]**](EntityTerm.md) | Values asserted for the property. | 

## Example

```python
from coa_control_plane_server.models.entity_property import EntityProperty

# TODO update the JSON string below
json = "{}"
# create an instance of EntityProperty from a JSON string
entity_property_instance = EntityProperty.from_json(json)
# print the JSON string representation of the object
print(EntityProperty.to_json())

# convert the object into a dict
entity_property_dict = entity_property_instance.to_dict()
# create an instance of EntityProperty from a dict
entity_property_from_dict = EntityProperty.from_dict(entity_property_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


