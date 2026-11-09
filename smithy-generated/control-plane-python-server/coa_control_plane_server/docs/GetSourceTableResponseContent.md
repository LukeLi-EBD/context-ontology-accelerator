# GetSourceTableResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**table_id** | **str** | Unique table identifier (database.table format). | 
**name** | **str** | Table name. | 
**database** | **str** | Database the table belongs to. | 
**review_status** | [**ReviewStatus**](ReviewStatus.md) |  | 
**columns** | [**List[ColumnMetadata]**](ColumnMetadata.md) | Metadata for every column in the table. | 
**business_metadata** | [**BusinessMetadataOutput**](BusinessMetadataOutput.md) |  | [optional] 
**primary_key** | [**PrimaryKeyOutput**](PrimaryKeyOutput.md) |  | [optional] 
**foreign_keys** | [**List[ForeignKeyOutput]**](ForeignKeyOutput.md) | Foreign-key relationships reported for the table. | [optional] 
**technical_metadata** | [**TechnicalMetadataOutput**](TechnicalMetadataOutput.md) |  | [optional] 
**pending_deletion** | **bool** | True when a re-scan found this table removed from the source; it is deleted on approve unless the steward keeps it. Absent/false otherwise. | [optional] 
**rescan_diff** | [**RescanTableDiff**](RescanTableDiff.md) |  | [optional] 
**added** | **bool** | True when the current re-scan discovered this table for the first time (it did not exist in the last approved scan). It therefore has no old-vs-new diff — the whole table is new. Absent/false otherwise. | [optional] 

## Example

```python
from coa_control_plane_server.models.get_source_table_response_content import GetSourceTableResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetSourceTableResponseContent from a JSON string
get_source_table_response_content_instance = GetSourceTableResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetSourceTableResponseContent.to_json())

# convert the object into a dict
get_source_table_response_content_dict = get_source_table_response_content_instance.to_dict()
# create an instance of GetSourceTableResponseContent from a dict
get_source_table_response_content_from_dict = GetSourceTableResponseContent.from_dict(get_source_table_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


