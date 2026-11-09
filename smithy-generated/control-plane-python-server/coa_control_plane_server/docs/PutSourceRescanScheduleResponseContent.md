# PutSourceRescanScheduleResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Identifier of the source. | 
**rescan_schedule** | [**RescanSchedule**](RescanSchedule.md) |  | 

## Example

```python
from coa_control_plane_server.models.put_source_rescan_schedule_response_content import PutSourceRescanScheduleResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of PutSourceRescanScheduleResponseContent from a JSON string
put_source_rescan_schedule_response_content_instance = PutSourceRescanScheduleResponseContent.from_json(json)
# print the JSON string representation of the object
print(PutSourceRescanScheduleResponseContent.to_json())

# convert the object into a dict
put_source_rescan_schedule_response_content_dict = put_source_rescan_schedule_response_content_instance.to_dict()
# create an instance of PutSourceRescanScheduleResponseContent from a dict
put_source_rescan_schedule_response_content_from_dict = PutSourceRescanScheduleResponseContent.from_dict(put_source_rescan_schedule_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


