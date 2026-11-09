# TranslateSPARQLRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** | Natural-language question to translate into SPARQL. | 

## Example

```python
from coa_data_layer_server.models.translate_sparql_request_content import TranslateSPARQLRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of TranslateSPARQLRequestContent from a JSON string
translate_sparql_request_content_instance = TranslateSPARQLRequestContent.from_json(json)
# print the JSON string representation of the object
print(TranslateSPARQLRequestContent.to_json())

# convert the object into a dict
translate_sparql_request_content_dict = translate_sparql_request_content_instance.to_dict()
# create an instance of TranslateSPARQLRequestContent from a dict
translate_sparql_request_content_from_dict = TranslateSPARQLRequestContent.from_dict(translate_sparql_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


