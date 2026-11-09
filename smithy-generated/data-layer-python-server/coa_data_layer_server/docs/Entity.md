# Entity

An entity (graph node) with its IRI, human-readable label, optional type, and arbitrary properties.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | IRI identifying the entity. | 
**label** | **str** | Human-readable label for the entity. | 
**type** | **str** | Type (class IRI) of the entity, if known. | [optional] 
**properties** | **Dict[str, str]** | String-valued entity properties. &#x60;supportingStatements&#x60; is reserved for a JSON-encoded string array of graph-only evidence. It is bounded to 100 statements per entity, 1,000 characters and 2,000 UTF-8 bytes per statement, and 4,000 characters and 6,000 UTF-8 bytes across an assembled graph context. | [optional] 

## Example

```python
from coa_data_layer_server.models.entity import Entity

# TODO update the JSON string below
json = "{}"
# create an instance of Entity from a JSON string
entity_instance = Entity.from_json(json)
# print the JSON string representation of the object
print(Entity.to_json())

# convert the object into a dict
entity_dict = entity_instance.to_dict()
# create an instance of Entity from a dict
entity_from_dict = Entity.from_dict(entity_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


