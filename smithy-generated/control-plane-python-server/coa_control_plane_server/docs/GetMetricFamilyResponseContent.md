# GetMetricFamilyResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**family** | [**MetricFamily**](MetricFamily.md) |  | 

## Example

```python
from coa_control_plane_server.models.get_metric_family_response_content import GetMetricFamilyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetMetricFamilyResponseContent from a JSON string
get_metric_family_response_content_instance = GetMetricFamilyResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetMetricFamilyResponseContent.to_json())

# convert the object into a dict
get_metric_family_response_content_dict = get_metric_family_response_content_instance.to_dict()
# create an instance of GetMetricFamilyResponseContent from a dict
get_metric_family_response_content_from_dict = GetMetricFamilyResponseContent.from_dict(get_metric_family_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


