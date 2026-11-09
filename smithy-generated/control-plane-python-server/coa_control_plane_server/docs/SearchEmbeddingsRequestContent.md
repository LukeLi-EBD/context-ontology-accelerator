# SearchEmbeddingsRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**vector** | **List[float]** | Query vector. Must have the same dimensionality as the stored rows. | 
**embedding_type** | **str** | Restrict the search to this vector kind. | 
**model_id** | **str** | Restrict the search to vectors from this model. | 
**entity_type** | **str** | Restrict the search to this entity type (engine default: &#x60;class&#x60;). | [optional] 
**ontology_id** | **str** | Restrict the search to one ontology&#39;s named graph. | [optional] 
**top_k** | **float** | Number of nearest rows to return (engine default: 10). | [optional] 

## Example

```python
from coa_control_plane_server.models.search_embeddings_request_content import SearchEmbeddingsRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of SearchEmbeddingsRequestContent from a JSON string
search_embeddings_request_content_instance = SearchEmbeddingsRequestContent.from_json(json)
# print the JSON string representation of the object
print(SearchEmbeddingsRequestContent.to_json())

# convert the object into a dict
search_embeddings_request_content_dict = search_embeddings_request_content_instance.to_dict()
# create an instance of SearchEmbeddingsRequestContent from a dict
search_embeddings_request_content_from_dict = SearchEmbeddingsRequestContent.from_dict(search_embeddings_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


