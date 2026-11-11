# FactBatchKeepRow

One group of a batch keep. `status` is one of `would_keep` (dry run), `kept`, or `skipped`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**subject** | **str** | IRI of a subject, predicate or object in the namespace A-Box. | 
**predicate** | **str** | IRI of a subject, predicate or object in the namespace A-Box. | 
**status** | **str** | One of &#x60;would_keep&#x60; (dry run), &#x60;kept&#x60;, or &#x60;skipped&#x60;. | 
**retired** | **float** | Facts retired by this row (0 for a skipped group). | [optional] 
**reason** | **str** | Why the group was skipped. | [optional] 
**values** | **List[str]** | Values the group had before the decision. | [optional] 
**kept_fact_ids** | **List[str]** | Assertion rows kept by a &#x60;kept&#x60; row; absent on a dry run. | [optional] 
**retired_fact_ids** | **List[str]** | Assertion rows retired by a &#x60;kept&#x60; row; absent on a dry run. | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_batch_keep_row import FactBatchKeepRow

# TODO update the JSON string below
json = "{}"
# create an instance of FactBatchKeepRow from a JSON string
fact_batch_keep_row_instance = FactBatchKeepRow.from_json(json)
# print the JSON string representation of the object
print(FactBatchKeepRow.to_json())

# convert the object into a dict
fact_batch_keep_row_dict = fact_batch_keep_row_instance.to_dict()
# create an instance of FactBatchKeepRow from a dict
fact_batch_keep_row_from_dict = FactBatchKeepRow.from_dict(fact_batch_keep_row_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


