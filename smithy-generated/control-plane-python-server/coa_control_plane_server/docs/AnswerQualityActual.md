# AnswerQualityActual

Actual answer produced for one golden-set case.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**refused** | **bool** | True when the answer was refused. | 
**answer_type** | **str** | Answer type chosen by the pipeline. | 
**answer_mode** | **str** | Answer mode chosen by the pipeline. | 
**reason_code** | **str** | Refusal reason code; absent when the answer was not refused. | [optional] 
**degraded** | **bool** | True when the answer was served degraded. | 
**citations** | [**List[AnswerQualityCitation]**](AnswerQualityCitation.md) | Citations attached to the answer. | 
**citation_kinds** | **List[str]** | Distinct citation kinds. | 
**missing_layers** | **List[str]** | Retrieval layers that produced nothing. | 

## Example

```python
from coa_control_plane_server.models.answer_quality_actual import AnswerQualityActual

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerQualityActual from a JSON string
answer_quality_actual_instance = AnswerQualityActual.from_json(json)
# print the JSON string representation of the object
print(AnswerQualityActual.to_json())

# convert the object into a dict
answer_quality_actual_dict = answer_quality_actual_instance.to_dict()
# create an instance of AnswerQualityActual from a dict
answer_quality_actual_from_dict = AnswerQualityActual.from_dict(answer_quality_actual_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


