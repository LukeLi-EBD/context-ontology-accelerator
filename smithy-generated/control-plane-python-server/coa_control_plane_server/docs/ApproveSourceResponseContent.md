# ApproveSourceResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Identifier of the source being approved. | 
**status** | [**SourceStatus**](SourceStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.approve_source_response_content import ApproveSourceResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ApproveSourceResponseContent from a JSON string
approve_source_response_content_instance = ApproveSourceResponseContent.from_json(json)
# print the JSON string representation of the object
print(ApproveSourceResponseContent.to_json())

# convert the object into a dict
approve_source_response_content_dict = approve_source_response_content_instance.to_dict()
# create an instance of ApproveSourceResponseContent from a dict
approve_source_response_content_from_dict = ApproveSourceResponseContent.from_dict(approve_source_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


