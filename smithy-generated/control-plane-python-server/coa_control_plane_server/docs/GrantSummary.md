# GrantSummary

A namespace grant record returned in responses, describing the principal, the role assigned to it, and any table allowlist, column denylist, or allowed-metrics scoping within the namespace.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**grant_id** | **str** | Unique identifier of the grant. | 
**namespace_id** | **str** | Identifier of the namespace the grant applies to. | 
**principal_type** | [**PrincipalType**](PrincipalType.md) |  | 
**principal_id** | **str** | Identifier of the principal the grant is bound to. | 
**role** | **str** | Name of the role assigned to the principal. | 
**granted_by** | **str** | Identifier of the principal that created the grant. | 
**granted_at** | **str** | Timestamp when the grant was created. | 
**table_allowlist** | **List[str]** | Optional list of tables the grant restricts data access to. | [optional] 
**column_denylist** | **Dict[str, List[str]]** |  | [optional] 
**allowed_metrics** | **List[str]** | Optional list of metrics the grant permits access to. | [optional] 

## Example

```python
from coa_control_plane_server.models.grant_summary import GrantSummary

# TODO update the JSON string below
json = "{}"
# create an instance of GrantSummary from a JSON string
grant_summary_instance = GrantSummary.from_json(json)
# print the JSON string representation of the object
print(GrantSummary.to_json())

# convert the object into a dict
grant_summary_dict = grant_summary_instance.to_dict()
# create an instance of GrantSummary from a dict
grant_summary_from_dict = GrantSummary.from_dict(grant_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


