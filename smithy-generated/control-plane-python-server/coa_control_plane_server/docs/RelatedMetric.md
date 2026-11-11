# RelatedMetric

One metric related to the entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_id** | **str** | Metric identifier. | 
**name_zh** | **str** | Chinese metric name. | [optional] 
**domain** | **str** | Metric domain. | [optional] 
**grain** | **str** | Metric grain. | [optional] 
**publishable** | **bool** | Whether the metric is publishable. | [optional] 
**bindings** | [**List[RelatedMetricBinding]**](RelatedMetricBinding.md) | Field bindings that connect the metric to the entity. | 
**match_basis** | **List[str]** | Why the metric matched the entity. | 

## Example

```python
from coa_control_plane_server.models.related_metric import RelatedMetric

# TODO update the JSON string below
json = "{}"
# create an instance of RelatedMetric from a JSON string
related_metric_instance = RelatedMetric.from_json(json)
# print the JSON string representation of the object
print(RelatedMetric.to_json())

# convert the object into a dict
related_metric_dict = related_metric_instance.to_dict()
# create an instance of RelatedMetric from a dict
related_metric_from_dict = RelatedMetric.from_dict(related_metric_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


