# AccessDeniedErrorResponseContent

Returned with HTTP 403 when the caller lacks permission to perform the requested operation.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the authorization failure. | 

## Example

```python
from coa_data_layer_server.models.access_denied_error_response_content import AccessDeniedErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of AccessDeniedErrorResponseContent from a JSON string
access_denied_error_response_content_instance = AccessDeniedErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(AccessDeniedErrorResponseContent.to_json())

# convert the object into a dict
access_denied_error_response_content_dict = access_denied_error_response_content_instance.to_dict()
# create an instance of AccessDeniedErrorResponseContent from a dict
access_denied_error_response_content_from_dict = AccessDeniedErrorResponseContent.from_dict(access_denied_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


