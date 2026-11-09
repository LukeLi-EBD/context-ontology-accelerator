# ColumnMetadata

Metadata describing a single column of a source table: its name, data type, nullability, partition-key flag, description, business metadata, and any sampled distinct values.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Column name. | 
**data_type** | **str** | Column data type (source-native type string). | 
**nullable** | **bool** | Whether the column permits null values. | [optional] 
**is_partition_key** | **bool** | Whether the column is a partition key. | [optional] 
**description** | **str** | Human-readable description of the column. | [optional] 
**business_metadata** | [**BusinessMetadataOutput**](BusinessMetadataOutput.md) |  | [optional] 
**distinct_values** | **List[str]** | Sampled distinct values for low-cardinality categorical columns (capped, best-effort). Empty for high-cardinality, non-string, or unsampled columns. Used by the serve NL→SQL layer to hint the LLM with correct enum literals for WHERE clauses, and shown in the UI. | [optional] 
**pending_deletion** | **bool** | True when a re-scan found this column removed from the source; it is deleted on approve unless the steward keeps it. Absent/false otherwise. | [optional] 

## Example

```python
from coa_control_plane_server.models.column_metadata import ColumnMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of ColumnMetadata from a JSON string
column_metadata_instance = ColumnMetadata.from_json(json)
# print the JSON string representation of the object
print(ColumnMetadata.to_json())

# convert the object into a dict
column_metadata_dict = column_metadata_instance.to_dict()
# create an instance of ColumnMetadata from a dict
column_metadata_from_dict = ColumnMetadata.from_dict(column_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


