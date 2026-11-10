# FindGraphPathResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**paths** | [**List[GraphPath]**](GraphPath.md) | Shortest paths first; each carries the nodes and edges to draw it. | 
**truncated** | **bool** | True when more paths exist than &#x60;&#x60;limit&#x60;&#x60; (or the search cap hit). | 

## Example

```python
from coa_control_plane_server.models.find_graph_path_response_content import FindGraphPathResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of FindGraphPathResponseContent from a JSON string
find_graph_path_response_content_instance = FindGraphPathResponseContent.from_json(json)
# print the JSON string representation of the object
print(FindGraphPathResponseContent.to_json())

# convert the object into a dict
find_graph_path_response_content_dict = find_graph_path_response_content_instance.to_dict()
# create an instance of FindGraphPathResponseContent from a dict
find_graph_path_response_content_from_dict = FindGraphPathResponseContent.from_dict(find_graph_path_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


