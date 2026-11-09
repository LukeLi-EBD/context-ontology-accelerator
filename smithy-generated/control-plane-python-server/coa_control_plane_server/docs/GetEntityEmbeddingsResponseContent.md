# GetEntityEmbeddingsResponseContent

Envelope for the embedding reads. The engine returns a bare array; the gateway wraps it in this structure to give the contract a typed output.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**embeddings** | [**List[EmbeddingRecord]**](EmbeddingRecord.md) | Matching embedding rows. | 

## Example

```python
from coa_control_plane_server.models.get_entity_embeddings_response_content import GetEntityEmbeddingsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetEntityEmbeddingsResponseContent from a JSON string
get_entity_embeddings_response_content_instance = GetEntityEmbeddingsResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetEntityEmbeddingsResponseContent.to_json())

# convert the object into a dict
get_entity_embeddings_response_content_dict = get_entity_embeddings_response_content_instance.to_dict()
# create an instance of GetEntityEmbeddingsResponseContent from a dict
get_entity_embeddings_response_content_from_dict = GetEntityEmbeddingsResponseContent.from_dict(get_entity_embeddings_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


