# UploadDocumentRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**filename** | **str** | Original filename, including extension. | 
**content_type** | **str** | MIME type of the uploaded bytes, e.g. &#x60;text/plain&#x60;. | 
**content_base64** | **str** | Base64-encoded document content. | [optional] 
**content_sha256** | **str** | SHA-256 of the content (lowercase hex). Optional when &#x60;contentBase64&#x60; is supplied — if present it must match the decoded bytes, and is rejected rather than ignored when it does not. | [optional] 
**title** | **str** | Display title; defaults to &#x60;filename&#x60;. | [optional] 
**metadata** | **Dict[str, str]** | Free-form document metadata carried through ingestion. | [optional] 

## Example

```python
from coa_control_plane_server.models.upload_document_request_content import UploadDocumentRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of UploadDocumentRequestContent from a JSON string
upload_document_request_content_instance = UploadDocumentRequestContent.from_json(json)
# print the JSON string representation of the object
print(UploadDocumentRequestContent.to_json())

# convert the object into a dict
upload_document_request_content_dict = upload_document_request_content_instance.to_dict()
# create an instance of UploadDocumentRequestContent from a dict
upload_document_request_content_from_dict = UploadDocumentRequestContent.from_dict(upload_document_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


