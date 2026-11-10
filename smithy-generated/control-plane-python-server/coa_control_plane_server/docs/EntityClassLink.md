# EntityClassLink

One superclass link in a class chain.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Class IRI. | 
**label** | **str** | Class label. | 

## Example

```python
from coa_control_plane_server.models.entity_class_link import EntityClassLink

# TODO update the JSON string below
json = "{}"
# create an instance of EntityClassLink from a JSON string
entity_class_link_instance = EntityClassLink.from_json(json)
# print the JSON string representation of the object
print(EntityClassLink.to_json())

# convert the object into a dict
entity_class_link_dict = entity_class_link_instance.to_dict()
# create an instance of EntityClassLink from a dict
entity_class_link_from_dict = EntityClassLink.from_dict(entity_class_link_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


