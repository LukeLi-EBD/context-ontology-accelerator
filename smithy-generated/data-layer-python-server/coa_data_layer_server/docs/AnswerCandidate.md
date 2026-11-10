# AnswerCandidate

A ranked candidate for the question as a whole.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**layer** | **str** | Layer the candidate belongs to. | 
**id** | **str** | Candidate identifier. | 
**label** | **str** | Human-readable label. | 
**reason** | **str** | Why the candidate matched. | 
**score** | **float** | Match score in 0..1. | 

## Example

```python
from coa_data_layer_server.models.answer_candidate import AnswerCandidate

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerCandidate from a JSON string
answer_candidate_instance = AnswerCandidate.from_json(json)
# print the JSON string representation of the object
print(AnswerCandidate.to_json())

# convert the object into a dict
answer_candidate_dict = answer_candidate_instance.to_dict()
# create an instance of AnswerCandidate from a dict
answer_candidate_from_dict = AnswerCandidate.from_dict(answer_candidate_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


