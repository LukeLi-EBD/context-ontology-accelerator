# AnswerQualityRun

One stored golden-set run. Every field is read from `platform.answer_quality_run`; nothing is recomputed at read time.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**run_id** | **str** | Stored run id (&#x60;platform.answer_quality_run.run_id&#x60;), the same value the quality response returned when the run was recorded. | 
**ran_at** | **datetime** | When the run finished, from &#x60;platform.answer_quality_run.ran_at&#x60;. | 
**strategy** | [**AnswerQualityStrategy**](AnswerQualityStrategy.md) |  | 
**golden_set** | **str** | Golden-set identifier, e.g. &#x60;r02-golden-10&#x60;. | 
**evaluated** | **float** | Cases evaluated in the run. | 
**passed** | **float** | Cases that passed. | 
**failed** | **float** | Cases that failed. | 
**pass_rate** | **float** | &#x60;passed / evaluated&#x60;, 0..1. | 
**citation_coverage_rate** | **float** | Share of cases with at least one citation, 0..1 (the run&#39;s overall coverage). | 
**citation_resolvable_rate** | **float** | Share of citations that resolve to a reachable target, 0..1. | 
**broken_link_rate** | **float** | Share of citations that do not resolve, 0..1. | 
**regression** | **bool** | True when the run recorded at least one broken citation. | 
**layer_coverage** | [**List[QualityLayerCoverage]**](QualityLayerCoverage.md) | Per-layer coverage. Absent for rows written before P14 started storing the aggregation in &#x60;detail&#x60;; absent means \&quot;not recorded\&quot;, never zero. | [optional] 

## Example

```python
from coa_control_plane_server.models.answer_quality_run import AnswerQualityRun

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerQualityRun from a JSON string
answer_quality_run_instance = AnswerQualityRun.from_json(json)
# print the JSON string representation of the object
print(AnswerQualityRun.to_json())

# convert the object into a dict
answer_quality_run_dict = answer_quality_run_instance.to_dict()
# create an instance of AnswerQualityRun from a dict
answer_quality_run_from_dict = AnswerQualityRun.from_dict(answer_quality_run_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


