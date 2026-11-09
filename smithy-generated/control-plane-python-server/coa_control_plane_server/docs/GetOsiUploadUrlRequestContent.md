# GetOsiUploadUrlRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**filename** | **str** | Original filename (used for content-type validation). | 

## Example

```python
from coa_control_plane_server.models.get_osi_upload_url_request_content import GetOsiUploadUrlRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOsiUploadUrlRequestContent from a JSON string
get_osi_upload_url_request_content_instance = GetOsiUploadUrlRequestContent.from_json(json)
# print the JSON string representation of the object
print(GetOsiUploadUrlRequestContent.to_json())

# convert the object into a dict
get_osi_upload_url_request_content_dict = get_osi_upload_url_request_content_instance.to_dict()
# create an instance of GetOsiUploadUrlRequestContent from a dict
get_osi_upload_url_request_content_from_dict = GetOsiUploadUrlRequestContent.from_dict(get_osi_upload_url_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


