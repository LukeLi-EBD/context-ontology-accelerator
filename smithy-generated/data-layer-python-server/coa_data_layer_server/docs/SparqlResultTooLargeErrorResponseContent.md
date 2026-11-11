# SparqlResultTooLargeErrorResponseContent

The result exceeded the 4 MiB response cap.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the size refusal. | 
**code** | **str** | Stable machine code: &#x60;E_SPARQL_RESULT_TOO_LARGE&#x60;. | 

## Example

```python
from coa_data_layer_server.models.sparql_result_too_large_error_response_content import SparqlResultTooLargeErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of SparqlResultTooLargeErrorResponseContent from a JSON string
sparql_result_too_large_error_response_content_instance = SparqlResultTooLargeErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(SparqlResultTooLargeErrorResponseContent.to_json())

# convert the object into a dict
sparql_result_too_large_error_response_content_dict = sparql_result_too_large_error_response_content_instance.to_dict()
# create an instance of SparqlResultTooLargeErrorResponseContent from a dict
sparql_result_too_large_error_response_content_from_dict = SparqlResultTooLargeErrorResponseContent.from_dict(sparql_result_too_large_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


