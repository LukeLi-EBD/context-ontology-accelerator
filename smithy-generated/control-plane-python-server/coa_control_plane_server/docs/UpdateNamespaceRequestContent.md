# UpdateNamespaceRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**display_name** | **str** | New human-readable display name for the namespace. An empty string clears it (the edit form sends \&quot;\&quot; for a cleared field). | [optional] 
**description** | **str** | New description for the namespace. An empty string clears it. | [optional] 

## Example

```python
from coa_control_plane_server.models.update_namespace_request_content import UpdateNamespaceRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateNamespaceRequestContent from a JSON string
update_namespace_request_content_instance = UpdateNamespaceRequestContent.from_json(json)
# print the JSON string representation of the object
print(UpdateNamespaceRequestContent.to_json())

# convert the object into a dict
update_namespace_request_content_dict = update_namespace_request_content_instance.to_dict()
# create an instance of UpdateNamespaceRequestContent from a dict
update_namespace_request_content_from_dict = UpdateNamespaceRequestContent.from_dict(update_namespace_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


