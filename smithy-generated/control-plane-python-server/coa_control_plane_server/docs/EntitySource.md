# EntitySource

One evidence source for the entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**kind** | **str** | Source family. | 
**ref** | **str** | Source reference. | 
**text** | **str** | Text span, when the source is a document chunk. | [optional] 
**resolve_url** | **str** | Console URL that resolves the reference. | 
**href** | **str** | Link intended for direct rendering. | 

## Example

```python
from coa_control_plane_server.models.entity_source import EntitySource

# TODO update the JSON string below
json = "{}"
# create an instance of EntitySource from a JSON string
entity_source_instance = EntitySource.from_json(json)
# print the JSON string representation of the object
print(EntitySource.to_json())

# convert the object into a dict
entity_source_dict = entity_source_instance.to_dict()
# create an instance of EntitySource from a dict
entity_source_from_dict = EntitySource.from_dict(entity_source_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


