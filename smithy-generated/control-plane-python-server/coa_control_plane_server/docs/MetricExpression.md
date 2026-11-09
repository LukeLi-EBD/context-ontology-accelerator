# MetricExpression

Expression container with multi-dialect support.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dialects** | [**List[MetricDialect]**](MetricDialect.md) | Per-dialect SQL expressions for the metric. | 

## Example

```python
from coa_control_plane_server.models.metric_expression import MetricExpression

# TODO update the JSON string below
json = "{}"
# create an instance of MetricExpression from a JSON string
metric_expression_instance = MetricExpression.from_json(json)
# print the JSON string representation of the object
print(MetricExpression.to_json())

# convert the object into a dict
metric_expression_dict = metric_expression_instance.to_dict()
# create an instance of MetricExpression from a dict
metric_expression_from_dict = MetricExpression.from_dict(metric_expression_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


