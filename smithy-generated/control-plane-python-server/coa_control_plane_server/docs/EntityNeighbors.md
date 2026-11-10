# EntityNeighbors

Immediate neighbourhood of an entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**nodes** | [**List[EntityNode]**](EntityNode.md) | Neighbour nodes. | 
**edges** | [**List[EntityEdge]**](EntityEdge.md) | Edges connecting them. | 
**truncated** | **bool** | True when the neighbourhood was capped by the request limit. | 

## Example

```python
from coa_control_plane_server.models.entity_neighbors import EntityNeighbors

# TODO update the JSON string below
json = "{}"
# create an instance of EntityNeighbors from a JSON string
entity_neighbors_instance = EntityNeighbors.from_json(json)
# print the JSON string representation of the object
print(EntityNeighbors.to_json())

# convert the object into a dict
entity_neighbors_dict = entity_neighbors_instance.to_dict()
# create an instance of EntityNeighbors from a dict
entity_neighbors_from_dict = EntityNeighbors.from_dict(entity_neighbors_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


