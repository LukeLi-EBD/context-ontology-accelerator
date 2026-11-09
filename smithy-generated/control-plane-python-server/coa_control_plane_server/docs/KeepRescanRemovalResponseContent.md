# KeepRescanRemovalResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**table_id** | **str** | Identifier of the table the kept item belongs to. | 
**column_name** | **str** | The kept column, echoed back only when keeping a single column. | [optional] 
**pending_deletion** | **bool** | The item&#39;s removal state after the keep. Always false — the item is no longer pending deletion. | 

## Example

```python
from coa_control_plane_server.models.keep_rescan_removal_response_content import KeepRescanRemovalResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of KeepRescanRemovalResponseContent from a JSON string
keep_rescan_removal_response_content_instance = KeepRescanRemovalResponseContent.from_json(json)
# print the JSON string representation of the object
print(KeepRescanRemovalResponseContent.to_json())

# convert the object into a dict
keep_rescan_removal_response_content_dict = keep_rescan_removal_response_content_instance.to_dict()
# create an instance of KeepRescanRemovalResponseContent from a dict
keep_rescan_removal_response_content_from_dict = KeepRescanRemovalResponseContent.from_dict(keep_rescan_removal_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


