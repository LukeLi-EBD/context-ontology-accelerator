# RescanTableDiff

The old-vs-new breakdown of what a re-scan changed for a table, so a Data Steward can compare against the last approved scan before approving. Present only while the source is in RESCAN_REVIEW and this table actually changed.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**table_fields** | [**List[RescanFieldChange]**](RescanFieldChange.md) | Changed table-level source-owned fields (description, keys, format, ...). | [optional] 
**columns** | [**List[RescanColumnChange]**](RescanColumnChange.md) | Per-column added / removed / modified breakdown. | [optional] 

## Example

```python
from coa_control_plane_server.models.rescan_table_diff import RescanTableDiff

# TODO update the JSON string below
json = "{}"
# create an instance of RescanTableDiff from a JSON string
rescan_table_diff_instance = RescanTableDiff.from_json(json)
# print the JSON string representation of the object
print(RescanTableDiff.to_json())

# convert the object into a dict
rescan_table_diff_dict = rescan_table_diff_instance.to_dict()
# create an instance of RescanTableDiff from a dict
rescan_table_diff_from_dict = RescanTableDiff.from_dict(rescan_table_diff_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


