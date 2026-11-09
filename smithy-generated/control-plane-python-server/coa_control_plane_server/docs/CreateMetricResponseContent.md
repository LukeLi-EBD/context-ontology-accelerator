# CreateMetricResponseContent

Result of creating a metric, including the persisted definition and any warnings.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric** | [**MetricDefinition**](MetricDefinition.md) |  | 
**warnings** | [**List[ValidationWarning]**](ValidationWarning.md) | Non-fatal validation warnings raised during creation. | [optional] 

## Example

```python
from coa_control_plane_server.models.create_metric_response_content import CreateMetricResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of CreateMetricResponseContent from a JSON string
create_metric_response_content_instance = CreateMetricResponseContent.from_json(json)
# print the JSON string representation of the object
print(CreateMetricResponseContent.to_json())

# convert the object into a dict
create_metric_response_content_dict = create_metric_response_content_instance.to_dict()
# create an instance of CreateMetricResponseContent from a dict
create_metric_response_content_from_dict = CreateMetricResponseContent.from_dict(create_metric_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


