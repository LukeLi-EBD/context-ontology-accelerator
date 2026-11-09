# CreateNamespaceResponseContent

Output of CreateNamespace, wrapping the newly created namespace detail.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**namespace** | [**NamespaceDetail**](NamespaceDetail.md) |  | 

## Example

```python
from coa_control_plane_server.models.create_namespace_response_content import CreateNamespaceResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of CreateNamespaceResponseContent from a JSON string
create_namespace_response_content_instance = CreateNamespaceResponseContent.from_json(json)
# print the JSON string representation of the object
print(CreateNamespaceResponseContent.to_json())

# convert the object into a dict
create_namespace_response_content_dict = create_namespace_response_content_instance.to_dict()
# create an instance of CreateNamespaceResponseContent from a dict
create_namespace_response_content_from_dict = CreateNamespaceResponseContent.from_dict(create_namespace_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


