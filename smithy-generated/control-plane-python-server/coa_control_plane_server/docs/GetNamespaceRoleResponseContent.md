# GetNamespaceRoleResponseContent

Output containing the requested role's detail.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**role** | [**RoleDetail**](RoleDetail.md) |  | 

## Example

```python
from coa_control_plane_server.models.get_namespace_role_response_content import GetNamespaceRoleResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetNamespaceRoleResponseContent from a JSON string
get_namespace_role_response_content_instance = GetNamespaceRoleResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetNamespaceRoleResponseContent.to_json())

# convert the object into a dict
get_namespace_role_response_content_dict = get_namespace_role_response_content_instance.to_dict()
# create an instance of GetNamespaceRoleResponseContent from a dict
get_namespace_role_response_content_from_dict = GetNamespaceRoleResponseContent.from_dict(get_namespace_role_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


