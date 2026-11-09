# UploadUrl

A pre-signed S3 PUT URL for a single file.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**filename** | **str** | Name of the file this URL is for. | 
**upload_url** | **str** | Pre-signed S3 PUT URL for uploading the file. | 

## Example

```python
from coa_control_plane_server.models.upload_url import UploadUrl

# TODO update the JSON string below
json = "{}"
# create an instance of UploadUrl from a JSON string
upload_url_instance = UploadUrl.from_json(json)
# print the JSON string representation of the object
print(UploadUrl.to_json())

# convert the object into a dict
upload_url_dict = upload_url_instance.to_dict()
# create an instance of UploadUrl from a dict
upload_url_from_dict = UploadUrl.from_dict(upload_url_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


