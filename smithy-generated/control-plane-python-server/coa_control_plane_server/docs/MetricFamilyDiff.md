# MetricFamilyDiff

One field that differs (or does not differ) across variants.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_field** | **str** | Field name used for the comparison. | 
**label** | **str** | Display label of the field. | 
**values** | **Dict[str, str]** | Rendered values of one diff field, keyed by variant metric id. | 
**different** | **bool** | True when the values are not all equal. | 

## Example

```python
from coa_control_plane_server.models.metric_family_diff import MetricFamilyDiff

# TODO update the JSON string below
json = "{}"
# create an instance of MetricFamilyDiff from a JSON string
metric_family_diff_instance = MetricFamilyDiff.from_json(json)
# print the JSON string representation of the object
print(MetricFamilyDiff.to_json())

# convert the object into a dict
metric_family_diff_dict = metric_family_diff_instance.to_dict()
# create an instance of MetricFamilyDiff from a dict
metric_family_diff_from_dict = MetricFamilyDiff.from_dict(metric_family_diff_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


