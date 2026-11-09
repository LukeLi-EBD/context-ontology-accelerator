# RateLimitExceededErrorResponseContent

Returned with HTTP 429 when the caller exceeds the request rate limit; `retryAfterSeconds` indicates how long to wait before retrying.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the error. | 
**retry_after_seconds** | **float** | Number of seconds to wait before retrying the request. | [optional] 

## Example

```python
from coa_data_layer_server.models.rate_limit_exceeded_error_response_content import RateLimitExceededErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RateLimitExceededErrorResponseContent from a JSON string
rate_limit_exceeded_error_response_content_instance = RateLimitExceededErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(RateLimitExceededErrorResponseContent.to_json())

# convert the object into a dict
rate_limit_exceeded_error_response_content_dict = rate_limit_exceeded_error_response_content_instance.to_dict()
# create an instance of RateLimitExceededErrorResponseContent from a dict
rate_limit_exceeded_error_response_content_from_dict = RateLimitExceededErrorResponseContent.from_dict(rate_limit_exceeded_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


