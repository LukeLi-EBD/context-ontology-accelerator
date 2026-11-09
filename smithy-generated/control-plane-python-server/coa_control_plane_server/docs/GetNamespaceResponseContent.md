# GetNamespaceResponseContent

Output of GetNamespace, wrapping the requested namespace detail.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**namespace** | [**NamespaceDetail**](NamespaceDetail.md) |  | 

## Example

```python
from coa_control_plane_server.models.get_namespace_response_content import GetNamespaceResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetNamespaceResponseContent from a JSON string
get_namespace_response_content_instance = GetNamespaceResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetNamespaceResponseContent.to_json())

# convert the object into a dict
get_namespace_response_content_dict = get_namespace_response_content_instance.to_dict()
# create an instance of GetNamespaceResponseContent from a dict
get_namespace_response_content_from_dict = GetNamespaceResponseContent.from_dict(get_namespace_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


