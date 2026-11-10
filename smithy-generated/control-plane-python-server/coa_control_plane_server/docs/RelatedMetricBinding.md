# RelatedMetricBinding

One metric field binding relevant to the entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**role** | **str** | Binding role. | [optional] 
**fact_table** | **str** | Fact table the metric reads. | [optional] 
**entity_column** | **str** | Column that holds the entity key. | [optional] 

## Example

```python
from coa_control_plane_server.models.related_metric_binding import RelatedMetricBinding

# TODO update the JSON string below
json = "{}"
# create an instance of RelatedMetricBinding from a JSON string
related_metric_binding_instance = RelatedMetricBinding.from_json(json)
# print the JSON string representation of the object
print(RelatedMetricBinding.to_json())

# convert the object into a dict
related_metric_binding_dict = related_metric_binding_instance.to_dict()
# create an instance of RelatedMetricBinding from a dict
related_metric_binding_from_dict = RelatedMetricBinding.from_dict(related_metric_binding_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


