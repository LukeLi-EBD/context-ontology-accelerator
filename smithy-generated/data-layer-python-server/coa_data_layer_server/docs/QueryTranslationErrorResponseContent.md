# QueryTranslationErrorResponseContent

Returned with HTTP 400 when a natural-language question cannot be translated into an executable query against the ontology.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the error. | 

## Example

```python
from coa_data_layer_server.models.query_translation_error_response_content import QueryTranslationErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of QueryTranslationErrorResponseContent from a JSON string
query_translation_error_response_content_instance = QueryTranslationErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(QueryTranslationErrorResponseContent.to_json())

# convert the object into a dict
query_translation_error_response_content_dict = query_translation_error_response_content_instance.to_dict()
# create an instance of QueryTranslationErrorResponseContent from a dict
query_translation_error_response_content_from_dict = QueryTranslationErrorResponseContent.from_dict(query_translation_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


