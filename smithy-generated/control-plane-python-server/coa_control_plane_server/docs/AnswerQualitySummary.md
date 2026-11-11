# AnswerQualitySummary

Aggregate rates over the run.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cases** | **float** | Number of cases in the run. | 
**passed** | **float** | Number of passing cases. | 
**failed** | **float** | Number of failing cases. | 
**pass_rate** | **float** | Share of passing cases (0-1). | 
**cases_with_citations** | **float** | Number of cases with at least one citation. | 
**citation_coverage_rate** | **float** | Share of cases with at least one citation (0-1). | 
**citations** | **float** | Total citations across the run. | 
**resolvable_citations** | **float** | Citations whose reference resolves. | 
**citation_resolvable_rate** | **float** | Share of citations that resolve (0-1). | 
**broken_link_rate** | **float** | Share of citations that do not resolve (0-1). | 
**baseline_broken_link_rate** | **float** | Broken-link rate recorded on the baseline. | 
**regression** | **bool** | True when the broken-link rate regressed against the baseline. | 

## Example

```python
from coa_control_plane_server.models.answer_quality_summary import AnswerQualitySummary

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerQualitySummary from a JSON string
answer_quality_summary_instance = AnswerQualitySummary.from_json(json)
# print the JSON string representation of the object
print(AnswerQualitySummary.to_json())

# convert the object into a dict
answer_quality_summary_dict = answer_quality_summary_instance.to_dict()
# create an instance of AnswerQualitySummary from a dict
answer_quality_summary_from_dict = AnswerQualitySummary.from_dict(answer_quality_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


