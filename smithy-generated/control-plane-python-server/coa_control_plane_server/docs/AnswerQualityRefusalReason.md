# AnswerQualityRefusalReason

Refusal count grouped by case type and reason code.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** | Case type. | 
**reason_code** | **str** | Refusal reason code. | 
**count** | **float** | Number of refusals. | 

## Example

```python
from coa_control_plane_server.models.answer_quality_refusal_reason import AnswerQualityRefusalReason

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerQualityRefusalReason from a JSON string
answer_quality_refusal_reason_instance = AnswerQualityRefusalReason.from_json(json)
# print the JSON string representation of the object
print(AnswerQualityRefusalReason.to_json())

# convert the object into a dict
answer_quality_refusal_reason_dict = answer_quality_refusal_reason_instance.to_dict()
# create an instance of AnswerQualityRefusalReason from a dict
answer_quality_refusal_reason_from_dict = AnswerQualityRefusalReason.from_dict(answer_quality_refusal_reason_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


