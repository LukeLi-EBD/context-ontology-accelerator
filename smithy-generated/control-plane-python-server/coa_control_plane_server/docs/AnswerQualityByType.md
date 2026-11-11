# AnswerQualityByType

Per-type aggregate used by the coverage and refusal breakdowns.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** | Case or answer type. | 
**cases** | **float** | Number of cases of this type. | 
**refused** | **float** | Number of refused answers of this type. | 
**with_citations** | **float** | Number of answers with citations, when applicable. | [optional] 
**citations** | **float** | Total citations of this type. | 
**resolvable** | **float** | Citations that resolve, when computed. | [optional] 
**citation_coverage_rate** | **float** | Share of cases with citations (0-1). | 
**resolvable_rate** | **float** | Share of citations that resolve (0-1), when computed. | [optional] 
**refusal_rate** | **float** | Share of answers refused (0-1), when computed. | [optional] 

## Example

```python
from coa_control_plane_server.models.answer_quality_by_type import AnswerQualityByType

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerQualityByType from a JSON string
answer_quality_by_type_instance = AnswerQualityByType.from_json(json)
# print the JSON string representation of the object
print(AnswerQualityByType.to_json())

# convert the object into a dict
answer_quality_by_type_dict = answer_quality_by_type_instance.to_dict()
# create an instance of AnswerQualityByType from a dict
answer_quality_by_type_from_dict = AnswerQualityByType.from_dict(answer_quality_by_type_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


