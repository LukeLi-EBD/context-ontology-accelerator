# MetricReportMeta

Counters and provenance for the whole manifest.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**generated_at** | **str** | Generation timestamp (ISO-8601). | 
**source** | **str** | Store the manifest was read from. | [optional] 
**scope** | **str** | Scope this manifest was generated for. | [optional] 
**total** | **float** | Number of rows in this response. | [optional] 
**all_total** | **float** | Number of rows in the namespace before filtering. | [optional] 
**counts** | [**MetricReportCounts**](MetricReportCounts.md) |  | [optional] 
**execution** | [**MetricReportExecution**](MetricReportExecution.md) |  | [optional] 
**industry_notice** | **str** | Industry-baseline notice shared by all industry rows. | [optional] 
**external_scope_rule** | **str** | Rule that decides external eligibility. | [optional] 
**disclaimer** | **str** | Statement that computability does not imply business values exist. | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_report_meta import MetricReportMeta

# TODO update the JSON string below
json = "{}"
# create an instance of MetricReportMeta from a JSON string
metric_report_meta_instance = MetricReportMeta.from_json(json)
# print the JSON string representation of the object
print(MetricReportMeta.to_json())

# convert the object into a dict
metric_report_meta_dict = metric_report_meta_instance.to_dict()
# create an instance of MetricReportMeta from a dict
metric_report_meta_from_dict = MetricReportMeta.from_dict(metric_report_meta_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


