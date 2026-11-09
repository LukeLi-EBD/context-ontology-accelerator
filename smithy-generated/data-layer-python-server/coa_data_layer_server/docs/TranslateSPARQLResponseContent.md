# TranslateSPARQLResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**sparql_query** | **str** | The SPARQL query generated from the question. | 
**confidence** | [**ConfidenceScore**](ConfidenceScore.md) |  | 
**trace** | [**List[TraceStep]**](TraceStep.md) | Step-by-step trace of the translation. | 
**ontology_version** | **str** | Version of the ontology the query was generated against. | [optional] 

## Example

```python
from coa_data_layer_server.models.translate_sparql_response_content import TranslateSPARQLResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of TranslateSPARQLResponseContent from a JSON string
translate_sparql_response_content_instance = TranslateSPARQLResponseContent.from_json(json)
# print the JSON string representation of the object
print(TranslateSPARQLResponseContent.to_json())

# convert the object into a dict
translate_sparql_response_content_dict = translate_sparql_response_content_instance.to_dict()
# create an instance of TranslateSPARQLResponseContent from a dict
translate_sparql_response_content_from_dict = TranslateSPARQLResponseContent.from_dict(translate_sparql_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


