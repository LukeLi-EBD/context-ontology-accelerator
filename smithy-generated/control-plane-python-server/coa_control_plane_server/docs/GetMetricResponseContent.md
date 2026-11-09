# GetMetricResponseContent

Result of retrieving a single metric definition.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric** | [**MetricDefinition**](MetricDefinition.md) |  | 

## Example

```python
from coa_control_plane_server.models.get_metric_response_content import GetMetricResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetMetricResponseContent from a JSON string
get_metric_response_content_instance = GetMetricResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetMetricResponseContent.to_json())

# convert the object into a dict
get_metric_response_content_dict = get_metric_response_content_instance.to_dict()
# create an instance of GetMetricResponseContent from a dict
get_metric_response_content_from_dict = GetMetricResponseContent.from_dict(get_metric_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


