# EntityProvenanceItem

One fact-ledger row backing a statement on the entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fact_id** | **str** | Assertion-row identifier. | 
**predicate** | **str** | Predicate IRI. | 
**object** | [**EntityTerm**](EntityTerm.md) |  | 
**state** | **str** | Ledger state of the row. | 
**source_kind** | **str** | Source family recorded on the row. | [optional] 
**document_id** | **str** | Document that produced the row. | [optional] 
**candidate_id** | **str** | Extraction candidate that produced the row. | [optional] 
**asserted_at** | **str** | When the row was asserted (ISO-8601). | 
**conflict** | **bool** | True when the row belongs to a conflict group. | 

## Example

```python
from coa_control_plane_server.models.entity_provenance_item import EntityProvenanceItem

# TODO update the JSON string below
json = "{}"
# create an instance of EntityProvenanceItem from a JSON string
entity_provenance_item_instance = EntityProvenanceItem.from_json(json)
# print the JSON string representation of the object
print(EntityProvenanceItem.to_json())

# convert the object into a dict
entity_provenance_item_dict = entity_provenance_item_instance.to_dict()
# create an instance of EntityProvenanceItem from a dict
entity_provenance_item_from_dict = EntityProvenanceItem.from_dict(entity_provenance_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


