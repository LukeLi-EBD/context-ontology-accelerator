# GetSourceUploadUrlsRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**files** | [**List[UploadFileRequest]**](UploadFileRequest.md) | Files to generate pre-signed upload URLs for. | 

## Example

```python
from coa_control_plane_server.models.get_source_upload_urls_request_content import GetSourceUploadUrlsRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetSourceUploadUrlsRequestContent from a JSON string
get_source_upload_urls_request_content_instance = GetSourceUploadUrlsRequestContent.from_json(json)
# print the JSON string representation of the object
print(GetSourceUploadUrlsRequestContent.to_json())

# convert the object into a dict
get_source_upload_urls_request_content_dict = get_source_upload_urls_request_content_instance.to_dict()
# create an instance of GetSourceUploadUrlsRequestContent from a dict
get_source_upload_urls_request_content_from_dict = GetSourceUploadUrlsRequestContent.from_dict(get_source_upload_urls_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


