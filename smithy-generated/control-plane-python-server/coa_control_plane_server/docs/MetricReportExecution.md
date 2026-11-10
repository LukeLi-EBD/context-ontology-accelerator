# MetricReportExecution

Execution-path breakdown of the manifest.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external_candidates** | **float** | Rows with external status external_candidate. | [optional] 
**executable_now** | **float** | Rows executable right now. | [optional] 
**rule_set_only** | **float** | Rows executable from a rule set only. | [optional] 
**unavailable** | **float** | Rows that cannot be executed yet. | [optional] 
**by_reason** | **Dict[str, float]** | Unavailable rows counted by reason code. | [optional] 
**basis** | **str** | Basis used by the execution judgement. | [optional] 
**note** | **str** | Explanatory note for the execution judgement. | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_report_execution import MetricReportExecution

# TODO update the JSON string below
json = "{}"
# create an instance of MetricReportExecution from a JSON string
metric_report_execution_instance = MetricReportExecution.from_json(json)
# print the JSON string representation of the object
print(MetricReportExecution.to_json())

# convert the object into a dict
metric_report_execution_dict = metric_report_execution_instance.to_dict()
# create an instance of MetricReportExecution from a dict
metric_report_execution_from_dict = MetricReportExecution.from_dict(metric_report_execution_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


