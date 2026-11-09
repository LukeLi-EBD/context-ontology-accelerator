# BulkDeleteFilter

Filter criteria selecting which metrics a bulk delete should remove.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data_source_id** | **str** | Delete all metrics with this data source ID. | [optional] 
**source_table** | **str** | Delete all metrics with this source table. | [optional] 
**name_prefix** | **str** | Delete all metrics whose name matches this prefix. | [optional] 

## Example

```python
from coa_control_plane_server.models.bulk_delete_filter import BulkDeleteFilter

# TODO update the JSON string below
json = "{}"
# create an instance of BulkDeleteFilter from a JSON string
bulk_delete_filter_instance = BulkDeleteFilter.from_json(json)
# print the JSON string representation of the object
print(BulkDeleteFilter.to_json())

# convert the object into a dict
bulk_delete_filter_dict = bulk_delete_filter_instance.to_dict()
# create an instance of BulkDeleteFilter from a dict
bulk_delete_filter_from_dict = BulkDeleteFilter.from_dict(bulk_delete_filter_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


