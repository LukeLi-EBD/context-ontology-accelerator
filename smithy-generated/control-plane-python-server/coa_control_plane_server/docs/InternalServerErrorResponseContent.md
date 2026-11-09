# InternalServerErrorResponseContent

Returned with HTTP 500 when the service fails unexpectedly. The message is a fixed, generic description; the underlying cause is logged, never returned.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Generic description of the failure; carries no internal detail. | 

## Example

```python
from coa_control_plane_server.models.internal_server_error_response_content import InternalServerErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of InternalServerErrorResponseContent from a JSON string
internal_server_error_response_content_instance = InternalServerErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(InternalServerErrorResponseContent.to_json())

# convert the object into a dict
internal_server_error_response_content_dict = internal_server_error_response_content_instance.to_dict()
# create an instance of InternalServerErrorResponseContent from a dict
internal_server_error_response_content_from_dict = InternalServerErrorResponseContent.from_dict(internal_server_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


