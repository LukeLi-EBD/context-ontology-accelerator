# MetricFamilyGuidance

Instruction shown when a family index is opened instead of a variant.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **str** | Stable machine code (for example E_METRIC_VARIANT_REQUIRED). | 
**message** | **str** | Human-readable explanation. | 
**how_to** | **List[str]** | Ordered steps that resolve the selection. | 

## Example

```python
from coa_control_plane_server.models.metric_family_guidance import MetricFamilyGuidance

# TODO update the JSON string below
json = "{}"
# create an instance of MetricFamilyGuidance from a JSON string
metric_family_guidance_instance = MetricFamilyGuidance.from_json(json)
# print the JSON string representation of the object
print(MetricFamilyGuidance.to_json())

# convert the object into a dict
metric_family_guidance_dict = metric_family_guidance_instance.to_dict()
# create an instance of MetricFamilyGuidance from a dict
metric_family_guidance_from_dict = MetricFamilyGuidance.from_dict(metric_family_guidance_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


