# DeleteNamespaceResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**namespace_id** | **str** | UUID v4 identifier. | 
**status** | [**NamespaceStatus**](NamespaceStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.delete_namespace_response_content import DeleteNamespaceResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of DeleteNamespaceResponseContent from a JSON string
delete_namespace_response_content_instance = DeleteNamespaceResponseContent.from_json(json)
# print the JSON string representation of the object
print(DeleteNamespaceResponseContent.to_json())

# convert the object into a dict
delete_namespace_response_content_dict = delete_namespace_response_content_instance.to_dict()
# create an instance of DeleteNamespaceResponseContent from a dict
delete_namespace_response_content_from_dict = DeleteNamespaceResponseContent.from_dict(delete_namespace_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


