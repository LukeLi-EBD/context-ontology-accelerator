# SearchEmbeddingsResponseContent

Envelope for the embedding reads. The engine returns a bare array; the gateway wraps it in this structure to give the contract a typed output.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**embeddings** | [**List[EmbeddingRecord]**](EmbeddingRecord.md) | Matching embedding rows. | 

## Example

```python
from coa_control_plane_server.models.search_embeddings_response_content import SearchEmbeddingsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of SearchEmbeddingsResponseContent from a JSON string
search_embeddings_response_content_instance = SearchEmbeddingsResponseContent.from_json(json)
# print the JSON string representation of the object
print(SearchEmbeddingsResponseContent.to_json())

# convert the object into a dict
search_embeddings_response_content_dict = search_embeddings_response_content_instance.to_dict()
# create an instance of SearchEmbeddingsResponseContent from a dict
search_embeddings_response_content_from_dict = SearchEmbeddingsResponseContent.from_dict(search_embeddings_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


