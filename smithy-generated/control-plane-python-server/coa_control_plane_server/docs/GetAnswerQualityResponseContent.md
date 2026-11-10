# GetAnswerQualityResponseContent

One answer-quality run over the fixed golden set.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**strategy** | **str** | Retrieval strategy used for the run. | 
**golden_set** | [**AnswerQualityGoldenSet**](AnswerQualityGoldenSet.md) |  | 
**summary** | [**AnswerQualitySummary**](AnswerQualitySummary.md) |  | 
**citation_coverage_by_type** | [**List[AnswerQualityByType]**](AnswerQualityByType.md) | Citation coverage grouped by case type. | [optional] 
**refusals_by_reason** | [**List[AnswerQualityRefusalReason]**](AnswerQualityRefusalReason.md) | Refusal counts grouped by reason. | [optional] 
**refusals_by_type** | [**List[AnswerQualityByType]**](AnswerQualityByType.md) | Refusal counts grouped by type. | [optional] 
**refusals_without_layers** | **List[object]** | Refusals that carried no layer diagnostics. | [optional] 
**broken_links** | **List[object]** | Citations that no longer resolve. | [optional] 
**cases** | [**List[AnswerQualityCase]**](AnswerQualityCase.md) | Per-case verdicts. | 
**empty** | **bool** | True when the run evaluated no cases. | 
**empty_reason** | **str** | Why the run is empty, when it is. | [optional] 
**read_only** | **bool** | Always true: the endpoint never writes. | 

## Example

```python
from coa_control_plane_server.models.get_answer_quality_response_content import GetAnswerQualityResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetAnswerQualityResponseContent from a JSON string
get_answer_quality_response_content_instance = GetAnswerQualityResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetAnswerQualityResponseContent.to_json())

# convert the object into a dict
get_answer_quality_response_content_dict = get_answer_quality_response_content_instance.to_dict()
# create an instance of GetAnswerQualityResponseContent from a dict
get_answer_quality_response_content_from_dict = GetAnswerQualityResponseContent.from_dict(get_answer_quality_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


