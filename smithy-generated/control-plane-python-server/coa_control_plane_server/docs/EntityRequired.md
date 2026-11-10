# EntityRequired

One property required by a class of the entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_property** | **str** | Property IRI. | 
**label** | **str** | Property label. | 
**min_count** | **float** | Minimum cardinality the class declares. | 
**declared_on** | **List[str]** | Classes that declare the requirement. | 
**values** | [**List[EntityTerm]**](EntityTerm.md) | Values present on the entity. | 
**value_count** | **float** | Number of values present. | 
**satisfied** | **bool** | True when &#x60;valueCount&#x60; meets &#x60;minCount&#x60;. | 

## Example

```python
from coa_control_plane_server.models.entity_required import EntityRequired

# TODO update the JSON string below
json = "{}"
# create an instance of EntityRequired from a JSON string
entity_required_instance = EntityRequired.from_json(json)
# print the JSON string representation of the object
print(EntityRequired.to_json())

# convert the object into a dict
entity_required_dict = entity_required_instance.to_dict()
# create an instance of EntityRequired from a dict
entity_required_from_dict = EntityRequired.from_dict(entity_required_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


