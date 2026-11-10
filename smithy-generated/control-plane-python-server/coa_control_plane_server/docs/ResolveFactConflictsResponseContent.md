# ResolveFactConflictsResponseContent

Outcome of one adjudication. Only the members for the chosen `action` are populated: `keep` fills kept/retired, `keep_both` fills acceptedFactIds, `merge` fills mergedFactId/originalFactIds, `batch` fills batch.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**action** | [**FactConflictAction**](FactConflictAction.md) |  | 
**subject** | **str** | Conflict group subject; absent on &#x60;batch&#x60; when the scope did not narrow by subject. | [optional] 
**predicate** | **str** | Conflict group predicate; absent on &#x60;batch&#x60; when the scope did not narrow by predicate. | [optional] 
**kept** | **str** | Value kept by &#x60;keep&#x60;. | [optional] 
**kept_fact_ids** | **List[str]** | Assertion rows kept by &#x60;keep&#x60;. | [optional] 
**retired_fact_ids** | **List[str]** | Assertion rows retired by &#x60;keep&#x60;. | [optional] 
**retired** | **float** | Number of retired rows (&#x60;keep&#x60;). | [optional] 
**values** | **List[str]** | Values the group had before the decision. | [optional] 
**accepted_fact_ids** | **List[str]** | Assertion rows accepted by &#x60;keep_both&#x60;. | [optional] 
**merged_fact_id** | **str** | New assertion row written by &#x60;merge&#x60;. | [optional] 
**original_fact_ids** | **List[str]** | Rows &#x60;merge&#x60; retired, in ledger order. | [optional] 
**batch** | [**FactBatchKeepResult**](FactBatchKeepResult.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.resolve_fact_conflicts_response_content import ResolveFactConflictsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ResolveFactConflictsResponseContent from a JSON string
resolve_fact_conflicts_response_content_instance = ResolveFactConflictsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ResolveFactConflictsResponseContent.to_json())

# convert the object into a dict
resolve_fact_conflicts_response_content_dict = resolve_fact_conflicts_response_content_instance.to_dict()
# create an instance of ResolveFactConflictsResponseContent from a dict
resolve_fact_conflicts_response_content_from_dict = ResolveFactConflictsResponseContent.from_dict(resolve_fact_conflicts_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


