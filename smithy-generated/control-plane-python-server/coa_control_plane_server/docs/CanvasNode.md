# CanvasNode

A drawable node: an IRI with an optional label and coarse kind.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | Full IRI of the node. | 
**label** | **str** | &#x60;&#x60;rdfs:label&#x60;&#x60; when one appears in the scanned page. | [optional] 
**kind** | **str** | &#x60;&#x60;class&#x60;&#x60;, &#x60;&#x60;object-property&#x60;&#x60;, &#x60;&#x60;datatype-property&#x60;&#x60;, or &#x60;&#x60;resource&#x60;&#x60; when the page&#39;s &#x60;&#x60;rdf:type&#x60;&#x60; triple does not name one of those. | [optional] 

## Example

```python
from coa_control_plane_server.models.canvas_node import CanvasNode

# TODO update the JSON string below
json = "{}"
# create an instance of CanvasNode from a JSON string
canvas_node_instance = CanvasNode.from_json(json)
# print the JSON string representation of the object
print(CanvasNode.to_json())

# convert the object into a dict
canvas_node_dict = canvas_node_instance.to_dict()
# create an instance of CanvasNode from a dict
canvas_node_from_dict = CanvasNode.from_dict(canvas_node_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


