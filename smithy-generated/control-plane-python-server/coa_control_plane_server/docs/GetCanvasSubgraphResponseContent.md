# GetCanvasSubgraphResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**nodes** | [**List[CanvasNode]**](CanvasNode.md) | Nodes touched by this page&#39;s triples. | 
**edges** | [**List[CanvasEdge]**](CanvasEdge.md) | Edges whose object is an IRI (literals are kept as node labels, never drawn as edges). | 
**truncated** | **bool** | True when another page exists beyond this window. | 
**node_count** | **float** | Number of nodes in this page (not the whole graph). | 
**edge_count** | **float** | Number of edges in this page (not the whole graph). | 
**next_offset** | **float** | Offset of the next page; present only when &#x60;&#x60;truncated&#x60;&#x60; is true. | [optional] 

## Example

```python
from coa_control_plane_server.models.get_canvas_subgraph_response_content import GetCanvasSubgraphResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetCanvasSubgraphResponseContent from a JSON string
get_canvas_subgraph_response_content_instance = GetCanvasSubgraphResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetCanvasSubgraphResponseContent.to_json())

# convert the object into a dict
get_canvas_subgraph_response_content_dict = get_canvas_subgraph_response_content_instance.to_dict()
# create an instance of GetCanvasSubgraphResponseContent from a dict
get_canvas_subgraph_response_content_from_dict = GetCanvasSubgraphResponseContent.from_dict(get_canvas_subgraph_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


