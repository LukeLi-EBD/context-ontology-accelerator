# DocumentSourceDetail

Type-specific detail for DOCUMENTS sources.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**s3_prefixes** | **List[str]** | S3 key prefixes ingested for this source. | [optional] 
**source_bucket_arn** | **str** | S3 bucket ARN. Format: arn:aws:s3:::{bucket-name} | [optional] 
**role_arn** | **str** | IAM role ARN for cross-account access. | [optional] 
**extraction_config** | [**ExtractionConfig**](ExtractionConfig.md) |  | [optional] 
**files_total** | **float** | Total number of files considered for ingestion. | [optional] 
**files_skipped** | **float** | Number of files skipped during preprocessing. | [optional] 
**files_errored** | **float** | Number of files that errored during preprocessing. | [optional] 
**error_message** | **str** | Error message if processing failed. | [optional] 
**preprocessing_issues** | [**List[PreprocessingIssue]**](PreprocessingIssue.md) | Per-file preprocessing issues recorded during ingestion. | [optional] 
**documents_processed** | **float** | Distinct source documents opened for chunk extraction by the KG build, read from the per-source metrics record (PK&#x3D;METRICS#{ns}, SK&#x3D;KGBUILD#{ds}). Null until the KG build has run and written metrics. | [optional] 
**chunks_llm** | **float** | Count of LLM extraction prompts run on chunks (topic + proposition each fire once per chunk, so this is ~&#x3D; extractors x chunks; NOT distinct). Null until the KG build has run. | [optional] 
**chunks_embed** | **float** | Distinct chunks whose embeddings were written to the OSS chunk vector index. Bounded by the true chunk count. Null until the KG build has run. | [optional] 
**chunks_graph** | **float** | Distinct chunk nodes inserted into the Neptune graph. Bounded by the true chunk count. Null until the KG build has run. | [optional] 

## Example

```python
from coa_control_plane_server.models.document_source_detail import DocumentSourceDetail

# TODO update the JSON string below
json = "{}"
# create an instance of DocumentSourceDetail from a JSON string
document_source_detail_instance = DocumentSourceDetail.from_json(json)
# print the JSON string representation of the object
print(DocumentSourceDetail.to_json())

# convert the object into a dict
document_source_detail_dict = document_source_detail_instance.to_dict()
# create an instance of DocumentSourceDetail from a dict
document_source_detail_from_dict = DocumentSourceDetail.from_dict(document_source_detail_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


