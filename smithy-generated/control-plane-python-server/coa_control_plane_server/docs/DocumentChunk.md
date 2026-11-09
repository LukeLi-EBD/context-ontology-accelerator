# DocumentChunk

One text chunk of a document.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**chunk_id** | **str** | Identifier of the chunk; also the entity URI suffix used by its embedding. | 
**page** | **float** | 1-based page number the chunk came from (1 for plain-text sources). | 
**text** | **str** | Chunk text exactly as indexed. | 
**char_start** | **float** | Inclusive character offset of the chunk in the normalised document text. | 
**char_end** | **float** | Exclusive character offset of the chunk in the normalised document text. | 

## Example

```python
from coa_control_plane_server.models.document_chunk import DocumentChunk

# TODO update the JSON string below
json = "{}"
# create an instance of DocumentChunk from a JSON string
document_chunk_instance = DocumentChunk.from_json(json)
# print the JSON string representation of the object
print(DocumentChunk.to_json())

# convert the object into a dict
document_chunk_dict = document_chunk_instance.to_dict()
# create an instance of DocumentChunk from a dict
document_chunk_from_dict = DocumentChunk.from_dict(document_chunk_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


