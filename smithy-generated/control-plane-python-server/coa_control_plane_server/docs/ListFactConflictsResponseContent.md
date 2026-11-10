# ListFactConflictsResponseContent

Conflict groups and their adjudication state.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**conflicts** | [**List[FactConflict]**](FactConflict.md) | Groups in ledger order. | 
**count** | **float** | Number of groups in this page. | 
**pending** | **float** | Groups that still need a decision. | 
**include_accepted** | **bool** | True when accepted conflicts were included. | [optional] 
**adjudications** | [**List[FactAdjudication]**](FactAdjudication.md) | Adjudication summary for every returned group. | [optional] 

## Example

```python
from coa_control_plane_server.models.list_fact_conflicts_response_content import ListFactConflictsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListFactConflictsResponseContent from a JSON string
list_fact_conflicts_response_content_instance = ListFactConflictsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListFactConflictsResponseContent.to_json())

# convert the object into a dict
list_fact_conflicts_response_content_dict = list_fact_conflicts_response_content_instance.to_dict()
# create an instance of ListFactConflictsResponseContent from a dict
list_fact_conflicts_response_content_from_dict = ListFactConflictsResponseContent.from_dict(list_fact_conflicts_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


