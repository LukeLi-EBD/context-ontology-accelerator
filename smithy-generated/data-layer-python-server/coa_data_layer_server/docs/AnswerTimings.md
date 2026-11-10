# AnswerTimings

Per-layer evaluation timings.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**terms_ms** | **float** | Ontology/term layer duration in milliseconds. | 
**metric_ms** | **float** | Metric matching duration in milliseconds. | 
**facts_ms** | **float** | Fact layer duration in milliseconds. | 

## Example

```python
from coa_data_layer_server.models.answer_timings import AnswerTimings

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerTimings from a JSON string
answer_timings_instance = AnswerTimings.from_json(json)
# print the JSON string representation of the object
print(AnswerTimings.to_json())

# convert the object into a dict
answer_timings_dict = answer_timings_instance.to_dict()
# create an instance of AnswerTimings from a dict
answer_timings_from_dict = AnswerTimings.from_dict(answer_timings_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


