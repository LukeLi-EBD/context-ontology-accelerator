# FactBatchKeepResult

Result of `batch`: the scope that was applied and what it touched.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**batch_id** | **str** | Identifier shared by every event this batch wrote. | 
**dry_run** | **bool** | True when nothing was written (the default). | 
**keep** | **str** | Value the rule keeps. | 
**matched** | **float** | Pending groups inside the scope. | 
**kept** | **float** | Groups kept (or that would be kept, on a dry run). | 
**skipped** | **float** | Groups where &#x60;keep&#x60; is not one of the values. | 
**affected_facts** | **float** | Facts retired across the matched groups. | 
**subject** | **str** | Scope the caller supplied; absent members did not narrow it. | [optional] 
**predicate** | **str** | IRI of a subject, predicate or object in the namespace A-Box. | [optional] 
**source_document_id** | **str** | UUID v4 identifier. | [optional] 
**results** | [**List[FactBatchKeepRow]**](FactBatchKeepRow.md) | Per-group outcome, in ledger order. | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_batch_keep_result import FactBatchKeepResult

# TODO update the JSON string below
json = "{}"
# create an instance of FactBatchKeepResult from a JSON string
fact_batch_keep_result_instance = FactBatchKeepResult.from_json(json)
# print the JSON string representation of the object
print(FactBatchKeepResult.to_json())

# convert the object into a dict
fact_batch_keep_result_dict = fact_batch_keep_result_instance.to_dict()
# create an instance of FactBatchKeepResult from a dict
fact_batch_keep_result_from_dict = FactBatchKeepResult.from_dict(fact_batch_keep_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


