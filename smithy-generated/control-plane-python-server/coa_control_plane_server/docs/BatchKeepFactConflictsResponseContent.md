# BatchKeepFactConflictsResponseContent

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
from coa_control_plane_server.models.batch_keep_fact_conflicts_response_content import BatchKeepFactConflictsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of BatchKeepFactConflictsResponseContent from a JSON string
batch_keep_fact_conflicts_response_content_instance = BatchKeepFactConflictsResponseContent.from_json(json)
# print the JSON string representation of the object
print(BatchKeepFactConflictsResponseContent.to_json())

# convert the object into a dict
batch_keep_fact_conflicts_response_content_dict = batch_keep_fact_conflicts_response_content_instance.to_dict()
# create an instance of BatchKeepFactConflictsResponseContent from a dict
batch_keep_fact_conflicts_response_content_from_dict = BatchKeepFactConflictsResponseContent.from_dict(batch_keep_fact_conflicts_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


