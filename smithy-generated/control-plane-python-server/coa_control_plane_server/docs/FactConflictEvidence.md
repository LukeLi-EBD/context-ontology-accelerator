# FactConflictEvidence

Text evidence attached to a conflicting row.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**chunk_id** | **str** | Chunk identifier inside the source document. | [optional] 
**text** | **str** | Text span that produced the value. | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_conflict_evidence import FactConflictEvidence

# TODO update the JSON string below
json = "{}"
# create an instance of FactConflictEvidence from a JSON string
fact_conflict_evidence_instance = FactConflictEvidence.from_json(json)
# print the JSON string representation of the object
print(FactConflictEvidence.to_json())

# convert the object into a dict
fact_conflict_evidence_dict = fact_conflict_evidence_instance.to_dict()
# create an instance of FactConflictEvidence from a dict
fact_conflict_evidence_from_dict = FactConflictEvidence.from_dict(fact_conflict_evidence_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


