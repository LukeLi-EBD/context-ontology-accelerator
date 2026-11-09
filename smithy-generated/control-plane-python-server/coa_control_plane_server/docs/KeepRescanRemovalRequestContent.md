# KeepRescanRemovalRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**column_name** | **str** | If set, keep only this removed column of the table. Omit to keep the whole removed table. | [optional] 

## Example

```python
from coa_control_plane_server.models.keep_rescan_removal_request_content import KeepRescanRemovalRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of KeepRescanRemovalRequestContent from a JSON string
keep_rescan_removal_request_content_instance = KeepRescanRemovalRequestContent.from_json(json)
# print the JSON string representation of the object
print(KeepRescanRemovalRequestContent.to_json())

# convert the object into a dict
keep_rescan_removal_request_content_dict = keep_rescan_removal_request_content_instance.to_dict()
# create an instance of KeepRescanRemovalRequestContent from a dict
keep_rescan_removal_request_content_from_dict = KeepRescanRemovalRequestContent.from_dict(keep_rescan_removal_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


