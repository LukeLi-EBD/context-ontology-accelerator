# RetractFactsResponseContent

Result of a batch retract.  `dryRun` defaults to true: an omitted flag can only preview. When `dryRun` is false, `batchId` is set and every retracted row shares it.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dry_run** | **bool** | True when the call only previewed the retract. | 
**batch_id** | **str** | Batch identifier written by the retract; absent on a dry run. | [optional] 
**count** | **float** | Number of rows that are (or would be) retracted. | 
**items** | [**List[FactRetractItem]**](FactRetractItem.md) | Rows that are (or would be) retracted. | 
**skipped** | [**List[FactRetractSkipped]**](FactRetractSkipped.md) | Rows filtered out of the selection. | 
**actor** | **str** | Identity recorded on the audit events. | 
**reason** | **str** | Why the rows were retracted. | [optional] 
**retracted** | **List[str]** | Identifiers of the retracted rows; absent on a dry run. | [optional] 

## Example

```python
from coa_control_plane_server.models.retract_facts_response_content import RetractFactsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RetractFactsResponseContent from a JSON string
retract_facts_response_content_instance = RetractFactsResponseContent.from_json(json)
# print the JSON string representation of the object
print(RetractFactsResponseContent.to_json())

# convert the object into a dict
retract_facts_response_content_dict = retract_facts_response_content_instance.to_dict()
# create an instance of RetractFactsResponseContent from a dict
retract_facts_response_content_from_dict = RetractFactsResponseContent.from_dict(retract_facts_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


