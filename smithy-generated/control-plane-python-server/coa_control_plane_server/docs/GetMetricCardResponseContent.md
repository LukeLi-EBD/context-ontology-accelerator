# GetMetricCardResponseContent

One governed metric definition with bindings and external-evidence status.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_id** | **str** | Stable metric identifier. | 
**name** | **str** | Chinese metric name. | [optional] 
**domain** | **str** | Metric domain. | [optional] 
**evidence_basis** | **str** | What kind of evidence backs the definition. | [optional] 
**publishable** | **bool** | Whether the metric may be published. | [optional] 
**inference** | **bool** | True when the metric is derived by inference rather than measured. | [optional] 
**formula_disabled** | **bool** | True when the formula is intentionally disabled. | [optional] 
**missing** | **str** | What is missing before the metric can be computed. | [optional] 
**evidence_status** | **str** | Evidence status recorded on the definition. | [optional] 
**note** | **str** | Operator note attached to the definition. | [optional] 
**effective_date** | **str** | Effective date of the definition (ISO-8601 date). | [optional] 
**variant_of** | **str** | Family index this metric is a variant of. | [optional] 
**output_mode** | **str** | Output mode: &#x60;single&#x60;, &#x60;index&#x60;, or &#x60;rule_set&#x60;. | [optional] 
**rule_set** | **object** | Rule-set payload; present only when &#x60;outputMode&#x60; is &#x60;rule_set&#x60;. | [optional] 
**definition** | **str** | Full prose definition. | [optional] 
**formula_text** | **str** | Formula as display text. | [optional] 
**denominator_text** | **str** | Denominator as display text. | [optional] 
**observation_period_text** | **str** | Observation period as display text. | [optional] 
**granularity_text** | **str** | Granularity as display text. | [optional] 
**grain** | **str** | Grain code matched against ontology class local names. | [optional] 
**provenance_label** | **str** | Provenance label. | [optional] 
**unit** | **str** | Unit of measure. | [optional] 
**definition_version** | **str** | Definition version. | [optional] 
**binding_status** | **str** | &#x60;bound&#x60; when at least one field binding exists, &#x60;unbound&#x60; otherwise. | 
**field_bindings** | [**List[MetricFieldBinding]**](MetricFieldBinding.md) | Physical bindings for this definition version. | 
**external_eligible** | **bool** | True when the metric passes the external-evidence gate. | [optional] 
**external_status** | **str** | External-evidence status code. | [optional] 
**external_label** | **str** | External-evidence status label. | [optional] 
**external_reason** | **str** | Why the metric is (not) external-eligible. | [optional] 
**family_id** | **str** | Family index this metric belongs to, when any. | [optional] 
**variant_metric_ids** | **List[str]** | Variant metric identifiers of the family. | 

## Example

```python
from coa_control_plane_server.models.get_metric_card_response_content import GetMetricCardResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetMetricCardResponseContent from a JSON string
get_metric_card_response_content_instance = GetMetricCardResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetMetricCardResponseContent.to_json())

# convert the object into a dict
get_metric_card_response_content_dict = get_metric_card_response_content_instance.to_dict()
# create an instance of GetMetricCardResponseContent from a dict
get_metric_card_response_content_from_dict = GetMetricCardResponseContent.from_dict(get_metric_card_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


