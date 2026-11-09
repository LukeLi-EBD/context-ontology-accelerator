# MetricDefinition

Full metric definition.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_id** | **str** | Server-assigned unique identifier. | [optional] 
**namespace_id** | **str** | Namespace this metric belongs to. | [optional] 
**name** | **str** | Metric name: alphanumeric + underscores, 1-128 chars. | 
**label** | **str** | Display-only label for the metric. Absent when the metric has none. | [optional] 
**description** | **str** | Human-readable description of what the metric measures. | 
**expression** | [**MetricExpression**](MetricExpression.md) |  | 
**data_source_id** | **str** | Data source identifier reference. | 
**source_table** | **str** | Source table name reference. | 
**default_time_grain** | [**TimeGrain**](TimeGrain.md) |  | [optional] 
**unit** | **str** | Unit of measure for the metric value (e.g. \&quot;USD\&quot;, \&quot;count\&quot;). | [optional] 
**return_type** | **str** | Data type of the value the metric returns (e.g. \&quot;integer\&quot;, \&quot;decimal\&quot;). | [optional] 
**ai_context** | [**MetricAiContext**](MetricAiContext.md) |  | [optional] 
**ontology_concepts** | **List[str]** | Ontology concept URIs this metric is associated with. | [optional] 
**defined_by** | **str** | Set by server — principal who created/updated the metric. | [optional] 
**effective_from** | **str** | Set by server — date the metric became effective. | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_definition import MetricDefinition

# TODO update the JSON string below
json = "{}"
# create an instance of MetricDefinition from a JSON string
metric_definition_instance = MetricDefinition.from_json(json)
# print the JSON string representation of the object
print(MetricDefinition.to_json())

# convert the object into a dict
metric_definition_dict = metric_definition_instance.to_dict()
# create an instance of MetricDefinition from a dict
metric_definition_from_dict = MetricDefinition.from_dict(metric_definition_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


