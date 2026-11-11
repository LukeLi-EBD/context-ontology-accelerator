# MetricFieldBinding

One physical binding of a metric to a fact-table column.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**role** | **str** | Role in the formula: &#x60;numerator&#x60;, &#x60;denominator&#x60;, or &#x60;index&#x60;. | [optional] 
**fact_table** | **str** | Fact table the binding reads. | [optional] 
**entity_column** | **str** | Column that holds the entity key. | [optional] 
**value_expr** | **str** | SQL expression that produces the value. | [optional] 
**agg** | **str** | Aggregate applied inside the window. | [optional] 
**filter_sql** | **str** | Additional SQL predicate. | [optional] 
**window_column** | **str** | Column used as the observation window. | [optional] 
**window_mode** | **str** | Window mode (e.g. &#x60;calendar&#x60;, &#x60;rolling&#x60;). | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_field_binding import MetricFieldBinding

# TODO update the JSON string below
json = "{}"
# create an instance of MetricFieldBinding from a JSON string
metric_field_binding_instance = MetricFieldBinding.from_json(json)
# print the JSON string representation of the object
print(MetricFieldBinding.to_json())

# convert the object into a dict
metric_field_binding_dict = metric_field_binding_instance.to_dict()
# create an instance of MetricFieldBinding from a dict
metric_field_binding_from_dict = MetricFieldBinding.from_dict(metric_field_binding_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


