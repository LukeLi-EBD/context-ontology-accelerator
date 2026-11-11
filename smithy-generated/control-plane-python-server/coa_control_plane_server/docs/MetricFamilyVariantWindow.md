# MetricFamilyVariantWindow

Observation window declared by a variant.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**kind** | **str** | Window kind (instant, period, rolling). | [optional] 
**min_window_days** | **float** | Minimum window length in days. | [optional] 
**text** | **str** | Rendered window description. | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_family_variant_window import MetricFamilyVariantWindow

# TODO update the JSON string below
json = "{}"
# create an instance of MetricFamilyVariantWindow from a JSON string
metric_family_variant_window_instance = MetricFamilyVariantWindow.from_json(json)
# print the JSON string representation of the object
print(MetricFamilyVariantWindow.to_json())

# convert the object into a dict
metric_family_variant_window_dict = metric_family_variant_window_instance.to_dict()
# create an instance of MetricFamilyVariantWindow from a dict
metric_family_variant_window_from_dict = MetricFamilyVariantWindow.from_dict(metric_family_variant_window_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


