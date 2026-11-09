# KBSearchResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**chunks** | [**List[SupportingContent]**](SupportingContent.md) | Ranked supporting chunks matching the query. | 
**trace** | [**List[TraceStep]**](TraceStep.md) | Step-by-step trace of the search. | 
**query_embedding_model** | **str** | Identifier of the embedding model used for the query. | [optional] 

## Example

```python
from coa_data_layer_server.models.kb_search_response_content import KBSearchResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of KBSearchResponseContent from a JSON string
kb_search_response_content_instance = KBSearchResponseContent.from_json(json)
# print the JSON string representation of the object
print(KBSearchResponseContent.to_json())

# convert the object into a dict
kb_search_response_content_dict = kb_search_response_content_instance.to_dict()
# create an instance of KBSearchResponseContent from a dict
kb_search_response_content_from_dict = KBSearchResponseContent.from_dict(kb_search_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


