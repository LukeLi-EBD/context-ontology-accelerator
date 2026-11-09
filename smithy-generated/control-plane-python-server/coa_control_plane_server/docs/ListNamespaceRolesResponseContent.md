# ListNamespaceRolesResponseContent

Output containing the list of roles within a namespace.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**roles** | [**List[RoleSummary]**](RoleSummary.md) | The roles available within the namespace. | 

## Example

```python
from coa_control_plane_server.models.list_namespace_roles_response_content import ListNamespaceRolesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListNamespaceRolesResponseContent from a JSON string
list_namespace_roles_response_content_instance = ListNamespaceRolesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListNamespaceRolesResponseContent.to_json())

# convert the object into a dict
list_namespace_roles_response_content_dict = list_namespace_roles_response_content_instance.to_dict()
# create an instance of ListNamespaceRolesResponseContent from a dict
list_namespace_roles_response_content_from_dict = ListNamespaceRolesResponseContent.from_dict(list_namespace_roles_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


