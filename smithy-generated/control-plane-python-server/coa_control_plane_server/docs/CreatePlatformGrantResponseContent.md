# CreatePlatformGrantResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**grant** | [**PlatformGrantSummary**](PlatformGrantSummary.md) |  | 

## Example

```python
from coa_control_plane_server.models.create_platform_grant_response_content import CreatePlatformGrantResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of CreatePlatformGrantResponseContent from a JSON string
create_platform_grant_response_content_instance = CreatePlatformGrantResponseContent.from_json(json)
# print the JSON string representation of the object
print(CreatePlatformGrantResponseContent.to_json())

# convert the object into a dict
create_platform_grant_response_content_dict = create_platform_grant_response_content_instance.to_dict()
# create an instance of CreatePlatformGrantResponseContent from a dict
create_platform_grant_response_content_from_dict = CreatePlatformGrantResponseContent.from_dict(create_platform_grant_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


