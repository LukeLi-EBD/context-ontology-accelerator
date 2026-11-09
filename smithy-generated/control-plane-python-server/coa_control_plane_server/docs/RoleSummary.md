# RoleSummary

Summary view of a role, returned in role listings.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**role_id** | **str** | Unique identifier of the role. | 
**name** | **str** | Human-readable role name (lowercase alphanumeric and hyphens). | 
**description** | **str** | Role description. | [optional] 
**scope** | [**RoleScope**](RoleScope.md) |  | 
**is_built_in** | **bool** | Whether this is a built-in role (true) or a custom role (false). | 

## Example

```python
from coa_control_plane_server.models.role_summary import RoleSummary

# TODO update the JSON string below
json = "{}"
# create an instance of RoleSummary from a JSON string
role_summary_instance = RoleSummary.from_json(json)
# print the JSON string representation of the object
print(RoleSummary.to_json())

# convert the object into a dict
role_summary_dict = role_summary_instance.to_dict()
# create an instance of RoleSummary from a dict
role_summary_from_dict = RoleSummary.from_dict(role_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


