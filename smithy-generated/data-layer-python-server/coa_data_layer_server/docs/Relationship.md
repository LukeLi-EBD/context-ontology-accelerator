# Relationship

A directed relationship between two entities, identified by source, predicate, and target IRIs.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_uri** | **str** | IRI of the source entity. | 
**predicate_uri** | **str** | IRI of the predicate linking source to target. A property-graph edge that carries only a human-readable predicate string is given a stable, tenant-scoped synthetic identifier in the &#x60;urn:coa:graph-predicate:&#x60; scheme, derived from that string. Treat such a value as an opaque identity for correlating edges within one namespace, not as an ontology predicate IRI. | 
**target_uri** | **str** | IRI of the target entity. | 
**predicate_label** | **str** | Human-readable label for the predicate. | [optional] 

## Example

```python
from coa_data_layer_server.models.relationship import Relationship

# TODO update the JSON string below
json = "{}"
# create an instance of Relationship from a JSON string
relationship_instance = Relationship.from_json(json)
# print the JSON string representation of the object
print(Relationship.to_json())

# convert the object into a dict
relationship_dict = relationship_instance.to_dict()
# create an instance of Relationship from a dict
relationship_from_dict = Relationship.from_dict(relationship_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


