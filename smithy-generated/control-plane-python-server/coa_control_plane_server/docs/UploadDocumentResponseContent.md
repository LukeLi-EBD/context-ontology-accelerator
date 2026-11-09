# UploadDocumentResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**document_id** | **str** | Identifier of the stored document. | 
**version** | **float** | Document version (1 for the first upload of these bytes). | 
**content_hash** | **str** | SHA-256 of the stored bytes, lowercase hex. | 
**status** | [**DocumentStatus**](DocumentStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.upload_document_response_content import UploadDocumentResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of UploadDocumentResponseContent from a JSON string
upload_document_response_content_instance = UploadDocumentResponseContent.from_json(json)
# print the JSON string representation of the object
print(UploadDocumentResponseContent.to_json())

# convert the object into a dict
upload_document_response_content_dict = upload_document_response_content_instance.to_dict()
# create an instance of UploadDocumentResponseContent from a dict
upload_document_response_content_from_dict = UploadDocumentResponseContent.from_dict(upload_document_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


