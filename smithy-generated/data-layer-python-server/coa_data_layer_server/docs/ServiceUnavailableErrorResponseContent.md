# ServiceUnavailableErrorResponseContent

Returned with HTTP 503 when the service, or a required dependency (including one it needs to handle the request safely), is temporarily unavailable. For example, a create that carries a `clientToken` fails closed with this error when the retry-safety store cannot be reached, rather than risk running the create twice. Retry the request (with the same `clientToken`) after a backoff.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Description of the unavailable dependency or operation; carries no internal detail. | 

## Example

```python
from coa_data_layer_server.models.service_unavailable_error_response_content import ServiceUnavailableErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ServiceUnavailableErrorResponseContent from a JSON string
service_unavailable_error_response_content_instance = ServiceUnavailableErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(ServiceUnavailableErrorResponseContent.to_json())

# convert the object into a dict
service_unavailable_error_response_content_dict = service_unavailable_error_response_content_instance.to_dict()
# create an instance of ServiceUnavailableErrorResponseContent from a dict
service_unavailable_error_response_content_from_dict = ServiceUnavailableErrorResponseContent.from_dict(service_unavailable_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


