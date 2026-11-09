# DeleteSourceResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Identifier of the deleted source. | [optional] 
**status** | [**SourceStatus**](SourceStatus.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.delete_source_response_content import DeleteSourceResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of DeleteSourceResponseContent from a JSON string
delete_source_response_content_instance = DeleteSourceResponseContent.from_json(json)
# print the JSON string representation of the object
print(DeleteSourceResponseContent.to_json())

# convert the object into a dict
delete_source_response_content_dict = delete_source_response_content_instance.to_dict()
# create an instance of DeleteSourceResponseContent from a dict
delete_source_response_content_from_dict = DeleteSourceResponseContent.from_dict(delete_source_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


