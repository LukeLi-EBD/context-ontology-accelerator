# GraphLinkEdge

One adjacency edge, tagged with the hop that discovered it.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source** | **str** | Subject IRI. | 
**predicate** | **str** | Predicate IRI. | 
**predicate_label** | **str** | Local name of the predicate, for display. | [optional] 
**target** | **str** | Object IRI. | 
**graph** | **str** | Named graph the triple lives in. | [optional] 
**direction** | **str** | How expansion traversed the edge: &#x60;&#x60;outgoing&#x60;&#x60; or &#x60;&#x60;incoming&#x60;&#x60;. | [optional] 
**hops** | **float** | Hop at which expansion discovered this edge (1–3). | 

## Example

```python
from coa_control_plane_server.models.graph_link_edge import GraphLinkEdge

# TODO update the JSON string below
json = "{}"
# create an instance of GraphLinkEdge from a JSON string
graph_link_edge_instance = GraphLinkEdge.from_json(json)
# print the JSON string representation of the object
print(GraphLinkEdge.to_json())

# convert the object into a dict
graph_link_edge_dict = graph_link_edge_instance.to_dict()
# create an instance of GraphLinkEdge from a dict
graph_link_edge_from_dict = GraphLinkEdge.from_dict(graph_link_edge_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


