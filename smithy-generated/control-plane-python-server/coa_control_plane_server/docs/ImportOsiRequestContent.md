# ImportOsiRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**content** | **str** | OSI YAML content as a string (inline). Mutually exclusive with s3Key. Maximum 5MB for inline content; use GetOsiUploadUrl + s3Key for larger files. | [optional] 
**s3_key** | **str** | S3 object key containing the OSI YAML (for large files uploaded via GetOsiUploadUrl). Mutually exclusive with content. | [optional] 
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original result instead of creating a duplicate; reusing the token with different parameters is rejected with ConflictError (409). | [optional] 

## Example

```python
from coa_control_plane_server.models.import_osi_request_content import ImportOsiRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ImportOsiRequestContent from a JSON string
import_osi_request_content_instance = ImportOsiRequestContent.from_json(json)
# print the JSON string representation of the object
print(ImportOsiRequestContent.to_json())

# convert the object into a dict
import_osi_request_content_dict = import_osi_request_content_instance.to_dict()
# create an instance of ImportOsiRequestContent from a dict
import_osi_request_content_from_dict = ImportOsiRequestContent.from_dict(import_osi_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


