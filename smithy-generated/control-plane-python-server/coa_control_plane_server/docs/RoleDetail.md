# RoleDetail

Full detail of a role, including its Cedar authorization policy.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**role_id** | **str** | Unique identifier of the role. | 
**name** | **str** | Human-readable role name (lowercase alphanumeric and hyphens). | 
**description** | **str** | Role description. | [optional] 
**scope** | [**RoleScope**](RoleScope.md) |  | 
**is_built_in** | **bool** | Whether this is a built-in role (true) or a custom role (false). | 
**cedar_policy** | **str** | The Cedar policy document defining the role&#39;s permissions. | [optional] 

## Example

```python
from coa_control_plane_server.models.role_detail import RoleDetail

# TODO update the JSON string below
json = "{}"
# create an instance of RoleDetail from a JSON string
role_detail_instance = RoleDetail.from_json(json)
# print the JSON string representation of the object
print(RoleDetail.to_json())

# convert the object into a dict
role_detail_dict = role_detail_instance.to_dict()
# create an instance of RoleDetail from a dict
role_detail_from_dict = RoleDetail.from_dict(role_detail_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


