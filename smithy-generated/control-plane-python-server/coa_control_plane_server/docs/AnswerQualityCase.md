# AnswerQualityCase

One golden-set case and its verdict.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Case identifier. | 
**query** | **str** | Query executed for the case. | 
**type** | **str** | Case type used for grouping. | 
**expect_refused** | **bool** | True when the case expects a refusal. | 
**actual** | [**AnswerQualityActual**](AnswerQualityActual.md) |  | 
**var_pass** | **bool** | True when the case passed. | 
**failures** | **List[str]** | Failure codes recorded for the case. | 
**drill_down_url** | **str** | Console URL for the underlying answer. | [optional] 

## Example

```python
from coa_control_plane_server.models.answer_quality_case import AnswerQualityCase

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerQualityCase from a JSON string
answer_quality_case_instance = AnswerQualityCase.from_json(json)
# print the JSON string representation of the object
print(AnswerQualityCase.to_json())

# convert the object into a dict
answer_quality_case_dict = answer_quality_case_instance.to_dict()
# create an instance of AnswerQualityCase from a dict
answer_quality_case_from_dict = AnswerQualityCase.from_dict(answer_quality_case_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


