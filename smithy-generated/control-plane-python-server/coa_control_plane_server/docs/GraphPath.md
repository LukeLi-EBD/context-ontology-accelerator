# GraphPath

One simple path: no node repeats, ``hops == edges.size()``.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**nodes** | [**List[CanvasNode]**](CanvasNode.md) | Nodes visited by the path, in traversal order. | 
**edges** | [**List[CanvasEdge]**](CanvasEdge.md) | Edges followed, one per hop; direction records assertion vs traversal. | 
**hops** | **float** | Number of edges in the path. | 

## Example

```python
from coa_control_plane_server.models.graph_path import GraphPath

# TODO update the JSON string below
json = "{}"
# create an instance of GraphPath from a JSON string
graph_path_instance = GraphPath.from_json(json)
# print the JSON string representation of the object
print(GraphPath.to_json())

# convert the object into a dict
graph_path_dict = graph_path_instance.to_dict()
# create an instance of GraphPath from a dict
graph_path_from_dict = GraphPath.from_dict(graph_path_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


