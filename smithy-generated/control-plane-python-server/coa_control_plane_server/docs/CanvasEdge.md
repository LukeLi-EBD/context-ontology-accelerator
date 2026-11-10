# CanvasEdge

A drawable edge. ``direction`` is ``outgoing`` for canvas pages and may be ``incoming`` on a path, where an edge is traversed against its assertion.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source** | **str** | Subject IRI. | 
**predicate** | **str** | Predicate IRI. | 
**predicate_label** | **str** | Local name of the predicate, for display. | [optional] 
**target** | **str** | Object IRI. | 
**graph** | **str** | Named graph the triple lives in. | [optional] 
**direction** | **str** | &#x60;&#x60;outgoing&#x60;&#x60; or &#x60;&#x60;incoming&#x60;&#x60;. | [optional] 

## Example

```python
from coa_control_plane_server.models.canvas_edge import CanvasEdge

# TODO update the JSON string below
json = "{}"
# create an instance of CanvasEdge from a JSON string
canvas_edge_instance = CanvasEdge.from_json(json)
# print the JSON string representation of the object
print(CanvasEdge.to_json())

# convert the object into a dict
canvas_edge_dict = canvas_edge_instance.to_dict()
# create an instance of CanvasEdge from a dict
canvas_edge_from_dict = CanvasEdge.from_dict(canvas_edge_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


