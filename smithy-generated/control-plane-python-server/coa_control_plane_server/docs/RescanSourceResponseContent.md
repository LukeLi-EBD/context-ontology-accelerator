# RescanSourceResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Identifier of the rescanned source. | [optional] 
**status** | [**SourceStatus**](SourceStatus.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.rescan_source_response_content import RescanSourceResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RescanSourceResponseContent from a JSON string
rescan_source_response_content_instance = RescanSourceResponseContent.from_json(json)
# print the JSON string representation of the object
print(RescanSourceResponseContent.to_json())

# convert the object into a dict
rescan_source_response_content_dict = rescan_source_response_content_instance.to_dict()
# create an instance of RescanSourceResponseContent from a dict
rescan_source_response_content_from_dict = RescanSourceResponseContent.from_dict(rescan_source_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


