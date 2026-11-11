# NotFoundErrorResponseContent

Returned with HTTP 404 when the requested resource does not exist.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of what was not found. | 

## Example

```python
from coa_data_layer_server.models.not_found_error_response_content import NotFoundErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of NotFoundErrorResponseContent from a JSON string
not_found_error_response_content_instance = NotFoundErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(NotFoundErrorResponseContent.to_json())

# convert the object into a dict
not_found_error_response_content_dict = not_found_error_response_content_instance.to_dict()
# create an instance of NotFoundErrorResponseContent from a dict
not_found_error_response_content_from_dict = NotFoundErrorResponseContent.from_dict(not_found_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


