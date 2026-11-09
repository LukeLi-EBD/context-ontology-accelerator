# GetSourceUploadUrlsResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**upload_id** | **str** | UUID v4 identifier. | 
**s3_prefix** | **str** | Relative S3 key prefix — no leading slash, no \&quot;..\&quot; traversal, no s3:// URI. Examples: \&quot;documents/\&quot;, \&quot;data/reports/2024/\&quot; | 
**upload_urls** | [**List[UploadUrl]**](UploadUrl.md) | Pre-signed S3 PUT URLs, one per requested file. | 
**expires_in** | **float** | Seconds until the generated URLs expire. | 

## Example

```python
from coa_control_plane_server.models.get_source_upload_urls_response_content import GetSourceUploadUrlsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetSourceUploadUrlsResponseContent from a JSON string
get_source_upload_urls_response_content_instance = GetSourceUploadUrlsResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetSourceUploadUrlsResponseContent.to_json())

# convert the object into a dict
get_source_upload_urls_response_content_dict = get_source_upload_urls_response_content_instance.to_dict()
# create an instance of GetSourceUploadUrlsResponseContent from a dict
get_source_upload_urls_response_content_from_dict = GetSourceUploadUrlsResponseContent.from_dict(get_source_upload_urls_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


