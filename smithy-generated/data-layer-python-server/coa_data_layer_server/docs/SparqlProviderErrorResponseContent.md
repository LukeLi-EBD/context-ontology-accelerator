# SparqlProviderErrorResponseContent

The provider could not execute the statement.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the provider failure. | 
**code** | **str** | Stable machine code: &#x60;E_SPARQL_PROVIDER_ERROR&#x60; or &#x60;E_SPARQL_PROVIDER_REJECTED&#x60;. | 
**provider_code** | **str** | The provider&#39;s own code, e.g. &#x60;HTTP_400&#x60;. | [optional] 
**provider_message** | **str** | The provider&#39;s own message, truncated for display. | [optional] 

## Example

```python
from coa_data_layer_server.models.sparql_provider_error_response_content import SparqlProviderErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of SparqlProviderErrorResponseContent from a JSON string
sparql_provider_error_response_content_instance = SparqlProviderErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(SparqlProviderErrorResponseContent.to_json())

# convert the object into a dict
sparql_provider_error_response_content_dict = sparql_provider_error_response_content_instance.to_dict()
# create an instance of SparqlProviderErrorResponseContent from a dict
sparql_provider_error_response_content_from_dict = SparqlProviderErrorResponseContent.from_dict(sparql_provider_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


