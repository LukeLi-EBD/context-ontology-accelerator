# CreateMetricRequestContent


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
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original result instead of creating a duplicate; reusing the token with different parameters is rejected with ConflictError (409). | [optional] 

## Example

```python
from coa_control_plane_server.models.create_metric_request_content import CreateMetricRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of CreateMetricRequestContent from a JSON string
create_metric_request_content_instance = CreateMetricRequestContent.from_json(json)
# print the JSON string representation of the object
print(CreateMetricRequestContent.to_json())

# convert the object into a dict
create_metric_request_content_dict = create_metric_request_content_instance.to_dict()
# create an instance of CreateMetricRequestContent from a dict
create_metric_request_content_from_dict = CreateMetricRequestContent.from_dict(create_metric_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


