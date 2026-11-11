# MetricReportItem

One governed metric row as it appears in the report manifest. Fields left absent were not applicable for that metric; they are never coerced to false.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_id** | **str** | Governed metric id (also the identifier used by /metrics/{metric_id}). | 
**name_zh** | **str** | Display name in Chinese. | [optional] 
**display_name** | **str** | Display label override, when the definition carries one. | [optional] 
**domain** | **str** | Business domain. | [optional] 
**publishable** | **bool** | Whether the metric may be published. | [optional] 
**evidence_basis** | **str** | Evidence basis (regulatory, industry, none). | [optional] 
**evidence_basis_label** | **str** | Rendered evidence-basis label. | [optional] 
**evidence_source** | **str** | Provenance label of the evidence. | [optional] 
**has_regulatory_text** | **bool** | True when regulatory text is attached. | [optional] 
**industry_baseline** | **bool** | True when the metric is an industry formula (internal baseline only). | [optional] 
**internal_notice** | **str** | Internal-baseline notice, when applicable. | [optional] 
**e1_baseline** | **bool** | True when the metric is flagged as an E1 baseline. | [optional] 
**formula** | **str** | Formula text as declared by the definition. | [optional] 
**formula_expr** | **str** | Formula expression used for execution, when declared. | [optional] 
**computability** | **str** | Computability tier code. | [optional] 
**computability_label** | **str** | Computability tier label. | [optional] 
**computability_tone** | **str** | Computability tone used by the UI (ok, warn, blocked). | [optional] 
**gap** | **str** | Short computability gap description. | [optional] 
**gap_code** | **str** | Stable gap code. | [optional] 
**missing** | **str** | Missing component description, when the metric cannot be computed. | [optional] 
**external_eligible** | **bool** | Whether the metric passes the external-eligibility rule. | [optional] 
**external_status** | **str** | Stable external status code. | [optional] 
**external_label** | **str** | Rendered external status label. | [optional] 
**external_reason** | **str** | Why the metric has this external status. | [optional] 
**execution_path** | **str** | Execution path code (unavailable, rule_set_only, executable). | [optional] 
**executable** | **bool** | True when the metric can be executed right now. | [optional] 
**execution_reason** | **str** | Human-readable execution blocker. | [optional] 
**execution_reason_code** | **str** | Stable execution blocker code. | [optional] 
**observation_count** | **float** | Number of observation rows available. | [optional] 
**available_window_days** | **float** | Observation window currently available, in days. | [optional] 
**min_window_days** | **float** | Observation window required by the definition, in days. | [optional] 
**window_sufficient** | **bool** | True when the available window covers the required window. | [optional] 
**window_warning** | **str** | Window warning shown to the reporter, when applicable. | [optional] 
**variant_of** | **str** | Family index id for a variant metric. | [optional] 
**output_mode** | **str** | Output mode (index, rule_set, value). | [optional] 
**formula_disabled** | **bool** | True when the formula exists but execution is disabled. | [optional] 
**inference** | **bool** | True when the definition is inferred rather than provided. | [optional] 
**evidence_status** | **str** | Evidence verification status. | [optional] 
**definition_version** | **str** | Definition version the row was read from. | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_report_item import MetricReportItem

# TODO update the JSON string below
json = "{}"
# create an instance of MetricReportItem from a JSON string
metric_report_item_instance = MetricReportItem.from_json(json)
# print the JSON string representation of the object
print(MetricReportItem.to_json())

# convert the object into a dict
metric_report_item_dict = metric_report_item_instance.to_dict()
# create an instance of MetricReportItem from a dict
metric_report_item_from_dict = MetricReportItem.from_dict(metric_report_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


