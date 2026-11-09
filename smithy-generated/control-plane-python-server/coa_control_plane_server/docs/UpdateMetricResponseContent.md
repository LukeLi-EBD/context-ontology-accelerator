# UpdateMetricResponseContent

Result of updating a metric, including the updated definition and any warnings.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric** | [**MetricDefinition**](MetricDefinition.md) |  | 
**warnings** | [**List[ValidationWarning]**](ValidationWarning.md) | Non-fatal validation warnings raised during the update. | [optional] 

## Example

```python
from coa_control_plane_server.models.update_metric_response_content import UpdateMetricResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateMetricResponseContent from a JSON string
update_metric_response_content_instance = UpdateMetricResponseContent.from_json(json)
# print the JSON string representation of the object
print(UpdateMetricResponseContent.to_json())

# convert the object into a dict
update_metric_response_content_dict = update_metric_response_content_instance.to_dict()
# create an instance of UpdateMetricResponseContent from a dict
update_metric_response_content_from_dict = UpdateMetricResponseContent.from_dict(update_metric_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


