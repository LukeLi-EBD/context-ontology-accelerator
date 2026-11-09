# ListDocumentChunksResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**items** | [**List[DocumentChunk]**](DocumentChunk.md) | Page of chunks, ordered by &#x60;charStart&#x60;. | 

## Example

```python
from coa_control_plane_server.models.list_document_chunks_response_content import ListDocumentChunksResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListDocumentChunksResponseContent from a JSON string
list_document_chunks_response_content_instance = ListDocumentChunksResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListDocumentChunksResponseContent.to_json())

# convert the object into a dict
list_document_chunks_response_content_dict = list_document_chunks_response_content_instance.to_dict()
# create an instance of ListDocumentChunksResponseContent from a dict
list_document_chunks_response_content_from_dict = ListDocumentChunksResponseContent.from_dict(list_document_chunks_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


