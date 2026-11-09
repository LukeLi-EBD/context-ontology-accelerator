# UpdateNamespaceResponseContent

Output of UpdateNamespace, wrapping the updated namespace detail.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**namespace** | [**NamespaceDetail**](NamespaceDetail.md) |  | 

## Example

```python
from coa_control_plane_server.models.update_namespace_response_content import UpdateNamespaceResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateNamespaceResponseContent from a JSON string
update_namespace_response_content_instance = UpdateNamespaceResponseContent.from_json(json)
# print the JSON string representation of the object
print(UpdateNamespaceResponseContent.to_json())

# convert the object into a dict
update_namespace_response_content_dict = update_namespace_response_content_instance.to_dict()
# create an instance of UpdateNamespaceResponseContent from a dict
update_namespace_response_content_from_dict = UpdateNamespaceResponseContent.from_dict(update_namespace_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


