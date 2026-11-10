# MetricFamily

One metric family (a family index plus its variants).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**family_id** | **str** | Family identifier, equal to the index metric id. | 
**index_metric_id** | **str** | The metric a caller lands on before choosing a variant. | 
**name_zh** | **str** | Display name of the family index. | [optional] 
**selection_required** | **bool** | Always true for a family index: output needs a variant metricId. | 
**guidance** | [**MetricFamilyGuidance**](MetricFamilyGuidance.md) |  | 
**variant_count** | **float** | Number of variants in this family. | 
**variants** | [**List[MetricFamilyVariant]**](MetricFamilyVariant.md) | Variants of this family, in metric id order. | 
**diffs** | [**List[MetricFamilyDiff]**](MetricFamilyDiff.md) | Field-by-field differences across variants. | 
**source** | **str** | Store the family was read from. | 

## Example

```python
from coa_control_plane_server.models.metric_family import MetricFamily

# TODO update the JSON string below
json = "{}"
# create an instance of MetricFamily from a JSON string
metric_family_instance = MetricFamily.from_json(json)
# print the JSON string representation of the object
print(MetricFamily.to_json())

# convert the object into a dict
metric_family_dict = metric_family_instance.to_dict()
# create an instance of MetricFamily from a dict
metric_family_from_dict = MetricFamily.from_dict(metric_family_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


