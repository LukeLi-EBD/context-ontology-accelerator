# DroppedTable

A table that could not be processed during induction.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**table_name** | **str** | Name of the table that was dropped. | 
**reason** | **str** | Short failure category, e.g. \&quot;gen_llm_empty\&quot; or \&quot;parse_failed\&quot;. | 

## Example

```python
from coa_control_plane_server.models.dropped_table import DroppedTable

# TODO update the JSON string below
json = "{}"
# create an instance of DroppedTable from a JSON string
dropped_table_instance = DroppedTable.from_json(json)
# print the JSON string representation of the object
print(DroppedTable.to_json())

# convert the object into a dict
dropped_table_dict = dropped_table_instance.to_dict()
# create an instance of DroppedTable from a dict
dropped_table_from_dict = DroppedTable.from_dict(dropped_table_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


