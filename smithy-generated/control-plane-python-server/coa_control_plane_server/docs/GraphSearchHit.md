# GraphSearchHit

A single result from a graph search query, identifying a matched vertex by its IRI, label, kind, and the named graph it lives in.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | IRI of the matched vertex. | 
**label** | **str** | Human-readable label of the matched vertex. | [optional] 
**kind** | **str** | Vertex kind (class, object-property, datatype-property, etc.). | 
**graph_uris** | **List[str]** | IRIs of the named graphs the vertex is defined in. A class IRI asserted in more than one ontology (e.g. a shared IRI referenced by both schema.org and FIBO) lists every source graph, not just one. | [optional] 

## Example

```python
from coa_control_plane_server.models.graph_search_hit import GraphSearchHit

# TODO update the JSON string below
json = "{}"
# create an instance of GraphSearchHit from a JSON string
graph_search_hit_instance = GraphSearchHit.from_json(json)
# print the JSON string representation of the object
print(GraphSearchHit.to_json())

# convert the object into a dict
graph_search_hit_dict = graph_search_hit_instance.to_dict()
# create an instance of GraphSearchHit from a dict
graph_search_hit_from_dict = GraphSearchHit.from_dict(graph_search_hit_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


