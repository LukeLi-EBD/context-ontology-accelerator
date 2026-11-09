# GraphNeighbor

A neighboring vertex reached by traversing an edge, identified by its IRI, label, and kind.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | IRI of the neighboring vertex. | 
**label** | **str** | Human-readable label of the neighboring vertex. | [optional] 
**kind** | **str** | Vertex kind of the neighbor. | 

## Example

```python
from coa_control_plane_server.models.graph_neighbor import GraphNeighbor

# TODO update the JSON string below
json = "{}"
# create an instance of GraphNeighbor from a JSON string
graph_neighbor_instance = GraphNeighbor.from_json(json)
# print the JSON string representation of the object
print(GraphNeighbor.to_json())

# convert the object into a dict
graph_neighbor_dict = graph_neighbor_instance.to_dict()
# create an instance of GraphNeighbor from a dict
graph_neighbor_from_dict = GraphNeighbor.from_dict(graph_neighbor_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


