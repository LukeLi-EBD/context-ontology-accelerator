# MatchedTerm

A term that matched part of the question.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**term** | **str** | Term IRI. | 
**label** | **str** | Human-readable label. | 
**span** | **List[float]** | Inclusive-exclusive [start, end) character span in the normalized question. | 

## Example

```python
from coa_data_layer_server.models.matched_term import MatchedTerm

# TODO update the JSON string below
json = "{}"
# create an instance of MatchedTerm from a JSON string
matched_term_instance = MatchedTerm.from_json(json)
# print the JSON string representation of the object
print(MatchedTerm.to_json())

# convert the object into a dict
matched_term_dict = matched_term_instance.to_dict()
# create an instance of MatchedTerm from a dict
matched_term_from_dict = MatchedTerm.from_dict(matched_term_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


