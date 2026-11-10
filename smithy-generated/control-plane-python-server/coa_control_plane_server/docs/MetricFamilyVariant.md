# MetricFamilyVariant

One variant of a metric family.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_id** | **str** | Variant metric id; use this for output calls. | 
**name_zh** | **str** | Display name of the variant. | [optional] 
**display_name** | **str** | Display label override, when the definition carries one. | [optional] 
**publishable** | **bool** | Whether the variant may be published at all. | [optional] 
**evidence_basis** | **str** | Evidence basis (regulatory, industry, none). | [optional] 
**external_eligible** | **bool** | Whether the variant passes the external-eligibility rule. | [optional] 
**internal_notice** | **str** | Notice shown when the variant is an internal baseline. | [optional] 
**formula** | **str** | Formula text as declared by the definition. | [optional] 
**formula_disabled** | **bool** | True when the formula is present but execution is disabled. | [optional] 
**computability** | **str** | Computability tier code. | [optional] 
**computability_label** | **str** | Computability tier label. | [optional] 
**window** | [**MetricFamilyVariantWindow**](MetricFamilyVariantWindow.md) |  | [optional] 
**denominator** | **str** | Denominator expression text, when the definition declares one. | [optional] 
**denominator_text** | **str** | Human-readable denominator description. | [optional] 
**grain** | **str** | Grain label (for example policy or agreement). | [optional] 
**grain_code** | **str** | Grain code as stored in the definition. | [optional] 
**metric_kind** | **str** | Metric kind (ratio, duration, sum, ...). | [optional] 
**unit** | **str** | Unit of the produced value. | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_family_variant import MetricFamilyVariant

# TODO update the JSON string below
json = "{}"
# create an instance of MetricFamilyVariant from a JSON string
metric_family_variant_instance = MetricFamilyVariant.from_json(json)
# print the JSON string representation of the object
print(MetricFamilyVariant.to_json())

# convert the object into a dict
metric_family_variant_dict = metric_family_variant_instance.to_dict()
# create an instance of MetricFamilyVariant from a dict
metric_family_variant_from_dict = MetricFamilyVariant.from_dict(metric_family_variant_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


