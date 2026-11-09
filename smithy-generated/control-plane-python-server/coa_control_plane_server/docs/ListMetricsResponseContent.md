# ListMetricsResponseContent

Paginated list of metric definitions.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**metrics** | [**List[MetricDefinition]**](MetricDefinition.md) | Metric definitions matching the request. | 

## Example

```python
from coa_control_plane_server.models.list_metrics_response_content import ListMetricsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListMetricsResponseContent from a JSON string
list_metrics_response_content_instance = ListMetricsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListMetricsResponseContent.to_json())

# convert the object into a dict
list_metrics_response_content_dict = list_metrics_response_content_instance.to_dict()
# create an instance of ListMetricsResponseContent from a dict
list_metrics_response_content_from_dict = ListMetricsResponseContent.from_dict(list_metrics_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


