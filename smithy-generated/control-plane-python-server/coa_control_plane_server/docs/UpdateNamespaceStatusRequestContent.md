# UpdateNamespaceStatusRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | [**NamespaceStatus**](NamespaceStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.update_namespace_status_request_content import UpdateNamespaceStatusRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateNamespaceStatusRequestContent from a JSON string
update_namespace_status_request_content_instance = UpdateNamespaceStatusRequestContent.from_json(json)
# print the JSON string representation of the object
print(UpdateNamespaceStatusRequestContent.to_json())

# convert the object into a dict
update_namespace_status_request_content_dict = update_namespace_status_request_content_instance.to_dict()
# create an instance of UpdateNamespaceStatusRequestContent from a dict
update_namespace_status_request_content_from_dict = UpdateNamespaceStatusRequestContent.from_dict(update_namespace_status_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


