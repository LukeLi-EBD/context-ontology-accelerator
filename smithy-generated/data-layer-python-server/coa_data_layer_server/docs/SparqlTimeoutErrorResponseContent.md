# SparqlTimeoutErrorResponseContent

The statement exceeded the 10 second limit.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the timeout. | 
**code** | **str** | Stable machine code: &#x60;E_SPARQL_TIMEOUT&#x60;. | 

## Example

```python
from coa_data_layer_server.models.sparql_timeout_error_response_content import SparqlTimeoutErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of SparqlTimeoutErrorResponseContent from a JSON string
sparql_timeout_error_response_content_instance = SparqlTimeoutErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(SparqlTimeoutErrorResponseContent.to_json())

# convert the object into a dict
sparql_timeout_error_response_content_dict = sparql_timeout_error_response_content_instance.to_dict()
# create an instance of SparqlTimeoutErrorResponseContent from a dict
sparql_timeout_error_response_content_from_dict = SparqlTimeoutErrorResponseContent.from_dict(sparql_timeout_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


