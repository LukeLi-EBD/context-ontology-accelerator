# PutSourceEventRescanResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Identifier of the source. | 
**event_rescan** | [**EventRescanConfig**](EventRescanConfig.md) |  | 

## Example

```python
from coa_control_plane_server.models.put_source_event_rescan_response_content import PutSourceEventRescanResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of PutSourceEventRescanResponseContent from a JSON string
put_source_event_rescan_response_content_instance = PutSourceEventRescanResponseContent.from_json(json)
# print the JSON string representation of the object
print(PutSourceEventRescanResponseContent.to_json())

# convert the object into a dict
put_source_event_rescan_response_content_dict = put_source_event_rescan_response_content_instance.to_dict()
# create an instance of PutSourceEventRescanResponseContent from a dict
put_source_event_rescan_response_content_from_dict = PutSourceEventRescanResponseContent.from_dict(put_source_event_rescan_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


