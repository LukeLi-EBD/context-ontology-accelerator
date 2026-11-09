# RescanSchedule

A recurring rescan cadence for a DATABASE source, backed by an EventBridge schedule. When enabled, the source is automatically re-scanned on the given cadence (a SCHEDULED-trigger rescan); the schema-diff keeps it non-destructive.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** | Whether the recurring rescan is currently active. | 
**schedule_expression** | **str** | EventBridge schedule expression, e.g. \&quot;rate(1 day)\&quot; or \&quot;cron(0 3 * * ? *)\&quot;. Required when enabled. | [optional] 
**timezone** | **str** | IANA timezone the cron expression is evaluated in (e.g. \&quot;America/New_York\&quot;). Defaults to UTC when omitted. | [optional] 

## Example

```python
from coa_control_plane_server.models.rescan_schedule import RescanSchedule

# TODO update the JSON string below
json = "{}"
# create an instance of RescanSchedule from a JSON string
rescan_schedule_instance = RescanSchedule.from_json(json)
# print the JSON string representation of the object
print(RescanSchedule.to_json())

# convert the object into a dict
rescan_schedule_dict = rescan_schedule_instance.to_dict()
# create an instance of RescanSchedule from a dict
rescan_schedule_from_dict = RescanSchedule.from_dict(rescan_schedule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


