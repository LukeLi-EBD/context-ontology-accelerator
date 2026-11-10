# EntityNode

One node in the immediate neighbourhood.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Node IRI. | 
**label** | **str** | Display label; falls back to the local name when unlabeled. | 
**inferred** | **bool** | True when the node exists only in the inferred graph. | 

## Example

```python
from coa_control_plane_server.models.entity_node import EntityNode

# TODO update the JSON string below
json = "{}"
# create an instance of EntityNode from a JSON string
entity_node_instance = EntityNode.from_json(json)
# print the JSON string representation of the object
print(EntityNode.to_json())

# convert the object into a dict
entity_node_dict = entity_node_instance.to_dict()
# create an instance of EntityNode from a dict
entity_node_from_dict = EntityNode.from_dict(entity_node_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


