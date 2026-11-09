# RescanFieldChange

One source-owned field that a re-scan changed vs. the last approved scan, carrying both the old and new values for the steward's before/after view.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_field** | **str** | Field name (e.g. \&quot;description\&quot;, \&quot;data_type\&quot;, \&quot;primary_key\&quot;). | 
**kind** | [**RescanChangeKind**](RescanChangeKind.md) |  | 
**old** | **str** | Value at the last approved scan. | [optional] 
**new** | **str** | Value the latest re-scan discovered. | [optional] 

## Example

```python
from coa_control_plane_server.models.rescan_field_change import RescanFieldChange

# TODO update the JSON string below
json = "{}"
# create an instance of RescanFieldChange from a JSON string
rescan_field_change_instance = RescanFieldChange.from_json(json)
# print the JSON string representation of the object
print(RescanFieldChange.to_json())

# convert the object into a dict
rescan_field_change_dict = rescan_field_change_instance.to_dict()
# create an instance of RescanFieldChange from a dict
rescan_field_change_from_dict = RescanFieldChange.from_dict(rescan_field_change_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


