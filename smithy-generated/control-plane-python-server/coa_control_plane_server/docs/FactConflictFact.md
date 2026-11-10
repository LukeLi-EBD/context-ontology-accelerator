# FactConflictFact

One fact backing a conflicting value.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fact_id** | **str** | Assertion-row identifier. | 
**object** | **str** | Object value this row asserts. | 
**object_kind** | **str** | &#x60;iri&#x60; or &#x60;literal&#x60;. | 
**source** | [**FactSource**](FactSource.md) |  | [optional] 
**asserted_at** | **str** | When the row was asserted (ISO-8601). | [optional] 
**evidence** | [**FactConflictEvidence**](FactConflictEvidence.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_conflict_fact import FactConflictFact

# TODO update the JSON string below
json = "{}"
# create an instance of FactConflictFact from a JSON string
fact_conflict_fact_instance = FactConflictFact.from_json(json)
# print the JSON string representation of the object
print(FactConflictFact.to_json())

# convert the object into a dict
fact_conflict_fact_dict = fact_conflict_fact_instance.to_dict()
# create an instance of FactConflictFact from a dict
fact_conflict_fact_from_dict = FactConflictFact.from_dict(fact_conflict_fact_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


