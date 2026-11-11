# EntityEdge

One edge in the immediate neighbourhood.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**s** | **str** | Subject IRI. | 
**p** | **str** | Predicate IRI. | 
**o** | **str** | Object IRI or lexical value. | 
**graph** | **str** | Named graph the edge came from. | 
**inferred** | **bool** | True when the edge exists only in the inferred graph. | 

## Example

```python
from coa_control_plane_server.models.entity_edge import EntityEdge

# TODO update the JSON string below
json = "{}"
# create an instance of EntityEdge from a JSON string
entity_edge_instance = EntityEdge.from_json(json)
# print the JSON string representation of the object
print(EntityEdge.to_json())

# convert the object into a dict
entity_edge_dict = entity_edge_instance.to_dict()
# create an instance of EntityEdge from a dict
entity_edge_from_dict = EntityEdge.from_dict(entity_edge_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


