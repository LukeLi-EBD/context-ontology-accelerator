# RescanColumnChange

A column a re-scan added, removed, or modified, with its changed fields.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Column name. | 
**status** | [**RescanColumnChangeStatus**](RescanColumnChangeStatus.md) |  | 
**fields** | [**List[RescanFieldChange]**](RescanFieldChange.md) | Changed source-owned fields (populated for MODIFIED). | [optional] 

## Example

```python
from coa_control_plane_server.models.rescan_column_change import RescanColumnChange

# TODO update the JSON string below
json = "{}"
# create an instance of RescanColumnChange from a JSON string
rescan_column_change_instance = RescanColumnChange.from_json(json)
# print the JSON string representation of the object
print(RescanColumnChange.to_json())

# convert the object into a dict
rescan_column_change_dict = rescan_column_change_instance.to_dict()
# create an instance of RescanColumnChange from a dict
rescan_column_change_from_dict = RescanColumnChange.from_dict(rescan_column_change_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


