# NamespaceNotFoundErrorResponseContent

Returned with HTTP 404 when the target namespace does not exist or is not visible to the caller.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the error. | 
**namespace_id** | **str** | Identifier of the namespace that was not found. | [optional] 

## Example

```python
from coa_data_layer_server.models.namespace_not_found_error_response_content import NamespaceNotFoundErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of NamespaceNotFoundErrorResponseContent from a JSON string
namespace_not_found_error_response_content_instance = NamespaceNotFoundErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(NamespaceNotFoundErrorResponseContent.to_json())

# convert the object into a dict
namespace_not_found_error_response_content_dict = namespace_not_found_error_response_content_instance.to_dict()
# create an instance of NamespaceNotFoundErrorResponseContent from a dict
namespace_not_found_error_response_content_from_dict = NamespaceNotFoundErrorResponseContent.from_dict(namespace_not_found_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


