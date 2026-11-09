# EventRescanConfig

Event-driven rescan configuration for a DATABASE source. When enabled (Glue sources only), upstream Glue Data Catalog changes to the source's database automatically trigger an EVENT-trigger rescan; the schema-diff keeps it non-destructive and repeated events are coalesced.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** | Whether event-driven rescans are currently active. | 

## Example

```python
from coa_control_plane_server.models.event_rescan_config import EventRescanConfig

# TODO update the JSON string below
json = "{}"
# create an instance of EventRescanConfig from a JSON string
event_rescan_config_instance = EventRescanConfig.from_json(json)
# print the JSON string representation of the object
print(EventRescanConfig.to_json())

# convert the object into a dict
event_rescan_config_dict = event_rescan_config_instance.to_dict()
# create an instance of EventRescanConfig from a dict
event_rescan_config_from_dict = EventRescanConfig.from_dict(event_rescan_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


