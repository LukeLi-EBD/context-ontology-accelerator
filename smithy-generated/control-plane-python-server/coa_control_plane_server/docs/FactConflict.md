# FactConflict

One (subject, predicate) group with more than one active value.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**subject** | **str** | Subject IRI shared by the group. | 
**predicate** | **str** | Predicate IRI shared by the group. | 
**values** | **List[str]** | Distinct values in the group. | 
**accepted** | **bool** | True when the group was accepted as a conflict without a single winner. | 
**pending** | **bool** | True when the group still needs a decision. | 
**facts** | [**List[FactConflictFact]**](FactConflictFact.md) | Rows backing the group. | 

## Example

```python
from coa_control_plane_server.models.fact_conflict import FactConflict

# TODO update the JSON string below
json = "{}"
# create an instance of FactConflict from a JSON string
fact_conflict_instance = FactConflict.from_json(json)
# print the JSON string representation of the object
print(FactConflict.to_json())

# convert the object into a dict
fact_conflict_dict = fact_conflict_instance.to_dict()
# create an instance of FactConflict from a dict
fact_conflict_from_dict = FactConflict.from_dict(fact_conflict_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


