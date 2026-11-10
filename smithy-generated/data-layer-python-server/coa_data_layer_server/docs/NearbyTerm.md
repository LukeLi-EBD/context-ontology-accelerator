# NearbyTerm

A lexically similar term offered for an uncovered fragment.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**term** | **str** | Term IRI. | 
**label** | **str** | Human-readable label. | 
**similarity** | **float** | Lexical similarity in 0..1. | 

## Example

```python
from coa_data_layer_server.models.nearby_term import NearbyTerm

# TODO update the JSON string below
json = "{}"
# create an instance of NearbyTerm from a JSON string
nearby_term_instance = NearbyTerm.from_json(json)
# print the JSON string representation of the object
print(NearbyTerm.to_json())

# convert the object into a dict
nearby_term_dict = nearby_term_instance.to_dict()
# create an instance of NearbyTerm from a dict
nearby_term_from_dict = NearbyTerm.from_dict(nearby_term_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


