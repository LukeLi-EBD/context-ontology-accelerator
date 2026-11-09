# GraphSearchResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**hits** | [**List[GraphSearchHit]**](GraphSearchHit.md) | The matching graph search hits (the requested page window). | 
**total_count** | **float** | Total number of hits matching the query across all pages, so a client can render a known page count. Independent of &#x60;&#x60;limit&#x60;&#x60; / &#x60;&#x60;offset&#x60;&#x60;. | [optional] 

## Example

```python
from coa_control_plane_server.models.graph_search_response_content import GraphSearchResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GraphSearchResponseContent from a JSON string
graph_search_response_content_instance = GraphSearchResponseContent.from_json(json)
# print the JSON string representation of the object
print(GraphSearchResponseContent.to_json())

# convert the object into a dict
graph_search_response_content_dict = graph_search_response_content_instance.to_dict()
# create an instance of GraphSearchResponseContent from a dict
graph_search_response_content_from_dict = GraphSearchResponseContent.from_dict(graph_search_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


