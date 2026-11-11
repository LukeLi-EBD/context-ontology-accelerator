# MetricReportFilters

Filters applied to a manifest response.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**scope** | **str** | Applied scope. | [optional] 
**domain** | **str** | Applied domain filter. | [optional] 
**evidence_basis** | **str** | Applied evidence-basis filter. | [optional] 
**publishable** | **bool** | Applied publishable filter. | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_report_filters import MetricReportFilters

# TODO update the JSON string below
json = "{}"
# create an instance of MetricReportFilters from a JSON string
metric_report_filters_instance = MetricReportFilters.from_json(json)
# print the JSON string representation of the object
print(MetricReportFilters.to_json())

# convert the object into a dict
metric_report_filters_dict = metric_report_filters_instance.to_dict()
# create an instance of MetricReportFilters from a dict
metric_report_filters_from_dict = MetricReportFilters.from_dict(metric_report_filters_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


