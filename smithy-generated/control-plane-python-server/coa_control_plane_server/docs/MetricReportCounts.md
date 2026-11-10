# MetricReportCounts

Counter breakdown of the manifest.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**publishable_true** | **float** | Rows with publishable&#x3D;true. | [optional] 
**industry** | **float** | Rows whose evidence basis is industry. | [optional] 
**regulatory** | **float** | Rows whose evidence basis is regulatory. | [optional] 
**external_eligible** | **float** | Rows that pass the external-eligibility rule. | [optional] 
**external_candidates** | **float** | Rows with external status external_candidate. | [optional] 
**executable_now** | **float** | Rows executable right now. | [optional] 
**industry_excluded_from_external** | **float** | Industry rows excluded from external output. | [optional] 
**computability** | **Dict[str, float]** | Row count per computability tier. | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_report_counts import MetricReportCounts

# TODO update the JSON string below
json = "{}"
# create an instance of MetricReportCounts from a JSON string
metric_report_counts_instance = MetricReportCounts.from_json(json)
# print the JSON string representation of the object
print(MetricReportCounts.to_json())

# convert the object into a dict
metric_report_counts_dict = metric_report_counts_instance.to_dict()
# create an instance of MetricReportCounts from a dict
metric_report_counts_from_dict = MetricReportCounts.from_dict(metric_report_counts_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


