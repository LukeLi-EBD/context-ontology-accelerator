# NoResultErrorResponseContent

Returned with HTTP 404 when a pinned tier produced no data for the query — a \"no results\" outcome rather than a server error.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the error. | 
**tier** | **float** | Pinned tier that produced no result (1 &#x3D; metric match, 2 &#x3D; structured query). | [optional] 

## Example

```python
from coa_data_layer_server.models.no_result_error_response_content import NoResultErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of NoResultErrorResponseContent from a JSON string
no_result_error_response_content_instance = NoResultErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(NoResultErrorResponseContent.to_json())

# convert the object into a dict
no_result_error_response_content_dict = no_result_error_response_content_instance.to_dict()
# create an instance of NoResultErrorResponseContent from a dict
no_result_error_response_content_from_dict = NoResultErrorResponseContent.from_dict(no_result_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


