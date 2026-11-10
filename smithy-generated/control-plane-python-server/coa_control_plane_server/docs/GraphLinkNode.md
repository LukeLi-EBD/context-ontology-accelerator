# GraphLinkNode

One neighbour reached from the seed IRI.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | Full IRI of the neighbour. | 
**label** | **str** | &#x60;&#x60;rdfs:label&#x60;&#x60; when the namespace carries one. | [optional] 
**kind** | **str** | &#x60;&#x60;class&#x60;&#x60;, &#x60;&#x60;object-property&#x60;&#x60;, &#x60;&#x60;datatype-property&#x60;&#x60; or &#x60;&#x60;resource&#x60;&#x60;. | [optional] 
**hops** | **float** | Shortest hop distance from the seed IRI (1–3). | 

## Example

```python
from coa_control_plane_server.models.graph_link_node import GraphLinkNode

# TODO update the JSON string below
json = "{}"
# create an instance of GraphLinkNode from a JSON string
graph_link_node_instance = GraphLinkNode.from_json(json)
# print the JSON string representation of the object
print(GraphLinkNode.to_json())

# convert the object into a dict
graph_link_node_dict = graph_link_node_instance.to_dict()
# create an instance of GraphLinkNode from a dict
graph_link_node_from_dict = GraphLinkNode.from_dict(graph_link_node_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


