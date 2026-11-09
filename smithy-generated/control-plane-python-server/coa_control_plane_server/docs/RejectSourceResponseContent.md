# RejectSourceResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Identifier of the source being rejected. | 
**status** | [**SourceStatus**](SourceStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.reject_source_response_content import RejectSourceResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RejectSourceResponseContent from a JSON string
reject_source_response_content_instance = RejectSourceResponseContent.from_json(json)
# print the JSON string representation of the object
print(RejectSourceResponseContent.to_json())

# convert the object into a dict
reject_source_response_content_dict = reject_source_response_content_instance.to_dict()
# create an instance of RejectSourceResponseContent from a dict
reject_source_response_content_from_dict = RejectSourceResponseContent.from_dict(reject_source_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


