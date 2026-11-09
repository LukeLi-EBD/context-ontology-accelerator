# ValidateMetricRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Metric name: alphanumeric + underscores, 1-128 chars. | 
**label** | **str** | Display-only label for the metric. Omit (or send null) for no label. | [optional] 
**description** | **str** | Human-readable description of what the metric measures. | 
**expression** | [**MetricExpression**](MetricExpression.md) |  | 
**data_source_id** | **str** | Data source identifier reference. | 
**source_table** | **str** | Source table name reference. | 
**default_time_grain** | [**TimeGrain**](TimeGrain.md) |  | [optional] 
**unit** | **str** | Unit of measure for the metric value (e.g. \&quot;USD\&quot;, \&quot;count\&quot;). | [optional] 
**return_type** | **str** | Data type of the value the metric returns (e.g. \&quot;integer\&quot;, \&quot;decimal\&quot;). | [optional] 
**ai_context** | [**MetricAiContext**](MetricAiContext.md) |  | [optional] 
**ontology_concepts** | **List[str]** | Ontology concept URIs this metric is associated with. | [optional] 

## Example

```python
from coa_control_plane_server.models.validate_metric_request_content import ValidateMetricRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ValidateMetricRequestContent from a JSON string
validate_metric_request_content_instance = ValidateMetricRequestContent.from_json(json)
# print the JSON string representation of the object
print(ValidateMetricRequestContent.to_json())

# convert the object into a dict
validate_metric_request_content_dict = validate_metric_request_content_instance.to_dict()
# create an instance of ValidateMetricRequestContent from a dict
validate_metric_request_content_from_dict = ValidateMetricRequestContent.from_dict(validate_metric_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


