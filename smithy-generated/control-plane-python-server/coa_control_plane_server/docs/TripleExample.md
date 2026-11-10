# TripleExample

One sampled triple.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**subject** | **str** | Subject IRI. | 
**predicate** | **str** | Predicate IRI. | 
**object** | **str** | Object IRI or lexical literal form. | 

## Example

```python
from coa_control_plane_server.models.triple_example import TripleExample

# TODO update the JSON string below
json = "{}"
# create an instance of TripleExample from a JSON string
triple_example_instance = TripleExample.from_json(json)
# print the JSON string representation of the object
print(TripleExample.to_json())

# convert the object into a dict
triple_example_dict = triple_example_instance.to_dict()
# create an instance of TripleExample from a dict
triple_example_from_dict = TripleExample.from_dict(triple_example_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


