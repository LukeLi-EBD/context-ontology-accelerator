# MetricDialect

A single dialect + expression pair.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dialect** | [**SqlDialect**](SqlDialect.md) |  | 
**expression** | **str** | SQL expression. Must be a full SELECT statement (or set operation) — e.g. \&quot;SELECT COUNT(*) AS total FROM orders\&quot;. Bare aggregate fragments like \&quot;COUNT(*)\&quot; are rejected: the serve-time SQL firewall only executes top-level SELECT statements, and onboarding validates the same shape. | 

## Example

```python
from coa_control_plane_server.models.metric_dialect import MetricDialect

# TODO update the JSON string below
json = "{}"
# create an instance of MetricDialect from a JSON string
metric_dialect_instance = MetricDialect.from_json(json)
# print the JSON string representation of the object
print(MetricDialect.to_json())

# convert the object into a dict
metric_dialect_dict = metric_dialect_instance.to_dict()
# create an instance of MetricDialect from a dict
metric_dialect_from_dict = MetricDialect.from_dict(metric_dialect_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


