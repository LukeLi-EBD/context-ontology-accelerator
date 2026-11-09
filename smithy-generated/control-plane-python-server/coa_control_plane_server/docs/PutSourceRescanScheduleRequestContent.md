# PutSourceRescanScheduleRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** | Whether the recurring rescan should be active. | 
**schedule_expression** | **str** | EventBridge schedule expression (e.g. \&quot;rate(1 day)\&quot; or \&quot;cron(0 3 * * ? *)\&quot;). Required when enabled&#x3D;true.  The cadence is floored, because every tick is a full discovery plus enrichment pass. A &#x60;rate()&#x60; below the floor is rejected with 400, a &#x60;cron()&#x60; must name a single minute so it cannot fire sub-hourly, and one-time &#x60;at()&#x60; expressions are not accepted. | [optional] 
**timezone** | **str** | IANA timezone for cron evaluation. Defaults to UTC. | [optional] 

## Example

```python
from coa_control_plane_server.models.put_source_rescan_schedule_request_content import PutSourceRescanScheduleRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of PutSourceRescanScheduleRequestContent from a JSON string
put_source_rescan_schedule_request_content_instance = PutSourceRescanScheduleRequestContent.from_json(json)
# print the JSON string representation of the object
print(PutSourceRescanScheduleRequestContent.to_json())

# convert the object into a dict
put_source_rescan_schedule_request_content_dict = put_source_rescan_schedule_request_content_instance.to_dict()
# create an instance of PutSourceRescanScheduleRequestContent from a dict
put_source_rescan_schedule_request_content_from_dict = PutSourceRescanScheduleRequestContent.from_dict(put_source_rescan_schedule_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


