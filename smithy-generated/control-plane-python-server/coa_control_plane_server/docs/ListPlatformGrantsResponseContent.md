# ListPlatformGrantsResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**grants** | [**List[PlatformGrantSummary]**](PlatformGrantSummary.md) | The page of platform grants. | 

## Example

```python
from coa_control_plane_server.models.list_platform_grants_response_content import ListPlatformGrantsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListPlatformGrantsResponseContent from a JSON string
list_platform_grants_response_content_instance = ListPlatformGrantsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListPlatformGrantsResponseContent.to_json())

# convert the object into a dict
list_platform_grants_response_content_dict = list_platform_grants_response_content_instance.to_dict()
# create an instance of ListPlatformGrantsResponseContent from a dict
list_platform_grants_response_content_from_dict = ListPlatformGrantsResponseContent.from_dict(list_platform_grants_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


