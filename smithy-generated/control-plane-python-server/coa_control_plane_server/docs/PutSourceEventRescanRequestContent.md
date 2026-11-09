# PutSourceEventRescanRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** | Whether event-driven rescans should be active. | 

## Example

```python
from coa_control_plane_server.models.put_source_event_rescan_request_content import PutSourceEventRescanRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of PutSourceEventRescanRequestContent from a JSON string
put_source_event_rescan_request_content_instance = PutSourceEventRescanRequestContent.from_json(json)
# print the JSON string representation of the object
print(PutSourceEventRescanRequestContent.to_json())

# convert the object into a dict
put_source_event_rescan_request_content_dict = put_source_event_rescan_request_content_instance.to_dict()
# create an instance of PutSourceEventRescanRequestContent from a dict
put_source_event_rescan_request_content_from_dict = PutSourceEventRescanRequestContent.from_dict(put_source_event_rescan_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


