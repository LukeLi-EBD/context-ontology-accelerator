# KBSearchRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** | Natural-language search query. | 
**top_k** | **float** | Maximum number of chunks to return. | [optional] 
**min_score** | **float** | Minimum relevance score a chunk must meet to be returned. Relevance scores are non-negative; no upper bound is set because the scale depends on the index&#39;s similarity metric. | [optional] 
**source_filter** | **List[str]** | Not yet supported; a non-empty value is rejected with 400. Reserved for restricting results to these source document identifiers. An empty list is accepted and restricts nothing. | [optional] 
**entity_filter** | **List[str]** | Not yet supported; a non-empty value is rejected with 400. Reserved for restricting results to chunks annotated with these entities. An empty list is accepted and restricts nothing. | [optional] 

## Example

```python
from coa_data_layer_server.models.kb_search_request_content import KBSearchRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of KBSearchRequestContent from a JSON string
kb_search_request_content_instance = KBSearchRequestContent.from_json(json)
# print the JSON string representation of the object
print(KBSearchRequestContent.to_json())

# convert the object into a dict
kb_search_request_content_dict = kb_search_request_content_instance.to_dict()
# create an instance of KBSearchRequestContent from a dict
kb_search_request_content_from_dict = KBSearchRequestContent.from_dict(kb_search_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


