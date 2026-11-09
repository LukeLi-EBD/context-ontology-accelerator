# ListPlatformRolesResponseContent

Output containing the list of platform-scoped roles.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**roles** | [**List[RoleSummary]**](RoleSummary.md) | The platform-scoped roles. | 

## Example

```python
from coa_control_plane_server.models.list_platform_roles_response_content import ListPlatformRolesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListPlatformRolesResponseContent from a JSON string
list_platform_roles_response_content_instance = ListPlatformRolesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListPlatformRolesResponseContent.to_json())

# convert the object into a dict
list_platform_roles_response_content_dict = list_platform_roles_response_content_instance.to_dict()
# create an instance of ListPlatformRolesResponseContent from a dict
list_platform_roles_response_content_from_dict = ListPlatformRolesResponseContent.from_dict(list_platform_roles_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


