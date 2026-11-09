# CreateDocumentSourceInput

Document source creation fields. For S3 sources: provide sourceBucketArn (and optionally s3Prefixes, roleArn). For upload sources: provide uploadId from GetSourceUploadUrls; the ingest prefix is derived server-side as {namespaceId}/raw/{uploadId}/ and any caller-supplied s3Prefixes is ignored.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Human-readable display name. Allows spaces and punctuation. 1–128 chars. | 
**s3_prefixes** | **List[str]** | S3 key prefixes to ingest. Used only for the S3 sub-type, where they point into the caller-owned sourceBucketArn. Ignored for upload sources, whose prefix is derived server-side from uploadId. | [optional] 
**upload_id** | **str** | Server-issued upload session identifier returned by GetSourceUploadUrls. Required for the upload sub-type; the ingest prefix is reconstructed as {namespaceId}/raw/{uploadId}/ so a caller cannot redirect ingestion at another namespace&#39;s objects. | [optional] 
**source_bucket_arn** | **str** | ARN of the S3 bucket. Required for S3 sub-type. | [optional] 
**role_arn** | **str** | IAM role for cross-account S3 access. | [optional] 
**extraction_config** | [**ExtractionConfig**](ExtractionConfig.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.create_document_source_input import CreateDocumentSourceInput

# TODO update the JSON string below
json = "{}"
# create an instance of CreateDocumentSourceInput from a JSON string
create_document_source_input_instance = CreateDocumentSourceInput.from_json(json)
# print the JSON string representation of the object
print(CreateDocumentSourceInput.to_json())

# convert the object into a dict
create_document_source_input_dict = create_document_source_input_instance.to_dict()
# create an instance of CreateDocumentSourceInput from a dict
create_document_source_input_from_dict = CreateDocumentSourceInput.from_dict(create_document_source_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


