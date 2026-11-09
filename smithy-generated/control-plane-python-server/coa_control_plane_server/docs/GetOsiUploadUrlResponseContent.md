# GetOsiUploadUrlResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**upload_url** | **str** | Pre-signed S3 PUT URL. Upload the YAML file here with Content-Type: application/x-yaml. | 
**s3_key** | **str** | S3 key to pass to ImportOsi after upload completes. | 
**expires_in** | **float** | Seconds until the pre-signed URL expires. | 

## Example

```python
from coa_control_plane_server.models.get_osi_upload_url_response_content import GetOsiUploadUrlResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOsiUploadUrlResponseContent from a JSON string
get_osi_upload_url_response_content_instance = GetOsiUploadUrlResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetOsiUploadUrlResponseContent.to_json())

# convert the object into a dict
get_osi_upload_url_response_content_dict = get_osi_upload_url_response_content_instance.to_dict()
# create an instance of GetOsiUploadUrlResponseContent from a dict
get_osi_upload_url_response_content_from_dict = GetOsiUploadUrlResponseContent.from_dict(get_osi_upload_url_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


