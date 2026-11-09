# GraphEdge

A relationship edge between two graph vertices, carrying the connecting predicate, its direction, and the neighboring vertex on the other end.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**predicate** | **str** | IRI of the connecting predicate. | 
**predicate_label** | **str** | Human-readable label of the predicate. | [optional] 
**direction** | **str** | Direction of the edge relative to the source vertex (incoming/outgoing). | 
**neighbor** | [**GraphNeighbor**](GraphNeighbor.md) |  | 

## Example

```python
from coa_control_plane_server.models.graph_edge import GraphEdge

# TODO update the JSON string below
json = "{}"
# create an instance of GraphEdge from a JSON string
graph_edge_instance = GraphEdge.from_json(json)
# print the JSON string representation of the object
print(GraphEdge.to_json())

# convert the object into a dict
graph_edge_dict = graph_edge_instance.to_dict()
# create an instance of GraphEdge from a dict
graph_edge_from_dict = GraphEdge.from_dict(graph_edge_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


