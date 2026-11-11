# MatchedTerm

A term that matched part of the question.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**term** | **str** | Term IRI. | 
**label** | **str** | Human-readable label. | 
**span** | **List[float]** | Inclusive-exclusive [start, end) character span in the normalized question. | 
**alias** | **str** | Surface that actually matched when it is an alias extracted from a bracketed label (\&quot;保单\&quot; from \&quot;保险合同（保单）\&quot;); absent when the whole label matched. | [optional] 
**candidates** | **List[str]** | Every concept that declares the matched surface when more than one does. &#x60;term&#x60; is then the deterministic primary (a real label outranks a derived alias, ties by IRI order); the others are not dropped silently. | [optional] 

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


