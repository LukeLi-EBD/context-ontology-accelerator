# AnswerQualityGoldenSet

The golden set that was evaluated.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Golden-set identifier. | 
**count** | **float** | Number of cases in the set. | 
**evaluated** | **float** | Number of cases evaluated in this run. | 
**case_id** | **str** | Identifier of the single case, when the run was narrowed to one case. | [optional] 

## Example

```python
from coa_control_plane_server.models.answer_quality_golden_set import AnswerQualityGoldenSet

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerQualityGoldenSet from a JSON string
answer_quality_golden_set_instance = AnswerQualityGoldenSet.from_json(json)
# print the JSON string representation of the object
print(AnswerQualityGoldenSet.to_json())

# convert the object into a dict
answer_quality_golden_set_dict = answer_quality_golden_set_instance.to_dict()
# create an instance of AnswerQualityGoldenSet from a dict
answer_quality_golden_set_from_dict = AnswerQualityGoldenSet.from_dict(answer_quality_golden_set_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


