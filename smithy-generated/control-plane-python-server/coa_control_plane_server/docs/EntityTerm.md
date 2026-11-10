# EntityTerm

One RDF term: IRI or literal (with optional datatype and language).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**kind** | **str** | &#x60;iri&#x60; or &#x60;literal&#x60;. | 
**value** | **str** | Lexical value of the term. | 
**iri** | **str** | IRI form; present when &#x60;kind&#x60; is &#x60;iri&#x60;. | [optional] 
**datatype** | **str** | Datatype IRI for typed literals. | [optional] 
**lang** | **str** | BCP-47 language tag for language-tagged literals. | [optional] 

## Example

```python
from coa_control_plane_server.models.entity_term import EntityTerm

# TODO update the JSON string below
json = "{}"
# create an instance of EntityTerm from a JSON string
entity_term_instance = EntityTerm.from_json(json)
# print the JSON string representation of the object
print(EntityTerm.to_json())

# convert the object into a dict
entity_term_dict = entity_term_instance.to_dict()
# create an instance of EntityTerm from a dict
entity_term_from_dict = EntityTerm.from_dict(entity_term_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


