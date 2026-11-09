# DocumentSummary

One document in the namespace's ingestion registry.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**document_id** | **str** | Identifier assigned by UploadDocument. | 
**title** | **str** | Display title (caller-supplied, else the filename). | 
**status** | [**DocumentStatus**](DocumentStatus.md) |  | 
**chunk_count** | **float** | Number of chunks written for this document. | 
**updated_at** | **float** | Timestamp of the last status change. | 

## Example

```python
from coa_control_plane_server.models.document_summary import DocumentSummary

# TODO update the JSON string below
json = "{}"
# create an instance of DocumentSummary from a JSON string
document_summary_instance = DocumentSummary.from_json(json)
# print the JSON string representation of the object
print(DocumentSummary.to_json())

# convert the object into a dict
document_summary_dict = document_summary_instance.to_dict()
# create an instance of DocumentSummary from a dict
document_summary_from_dict = DocumentSummary.from_dict(document_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


