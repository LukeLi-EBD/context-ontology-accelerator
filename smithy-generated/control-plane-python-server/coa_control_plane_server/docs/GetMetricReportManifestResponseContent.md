# GetMetricReportManifestResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[MetricReportItem]**](MetricReportItem.md) | Manifest rows after filtering. | 
**count** | **float** | Number of rows in items. | 
**meta** | [**MetricReportMeta**](MetricReportMeta.md) |  | 
**filters** | [**MetricReportFilters**](MetricReportFilters.md) |  | 

## Example

```python
from coa_control_plane_server.models.get_metric_report_manifest_response_content import GetMetricReportManifestResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetMetricReportManifestResponseContent from a JSON string
get_metric_report_manifest_response_content_instance = GetMetricReportManifestResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetMetricReportManifestResponseContent.to_json())

# convert the object into a dict
get_metric_report_manifest_response_content_dict = get_metric_report_manifest_response_content_instance.to_dict()
# create an instance of GetMetricReportManifestResponseContent from a dict
get_metric_report_manifest_response_content_from_dict = GetMetricReportManifestResponseContent.from_dict(get_metric_report_manifest_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


