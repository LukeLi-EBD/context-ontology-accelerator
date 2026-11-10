# FactObject

RDF object of an assertion row.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**kind** | **str** | &#x60;iri&#x60; or &#x60;literal&#x60;. | 
**value** | **str** | Lexical value of the object. | 
**iri** | **str** | IRI form of the object; present when &#x60;kind&#x60; is &#x60;iri&#x60;. | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_object import FactObject

# TODO update the JSON string below
json = "{}"
# create an instance of FactObject from a JSON string
fact_object_instance = FactObject.from_json(json)
# print the JSON string representation of the object
print(FactObject.to_json())

# convert the object into a dict
fact_object_dict = fact_object_instance.to_dict()
# create an instance of FactObject from a dict
fact_object_from_dict = FactObject.from_dict(fact_object_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


