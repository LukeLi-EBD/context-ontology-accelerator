# ForeignKeyInput

Steward-supplied foreign key relationship. Stored with source = STEWARD_SPECIFIED.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**column** | **str** | Column name identifier. | 
**target_table** | **str** | Referenced table. | 
**target_column** | **str** | Referenced column in the target table. | [optional] 
**source** | **str** | Origin of the key. Preserved on a steward review so an approved inferred relationship keeps its AI_INFERRED provenance (#1088). | [optional] 
**review_status** | **str** | Steward review decision for an inferred relationship (#1088): APPROVED or REJECTED. Omitted for a plain steward-authored edit (treated as approved). | [optional] 
**target_datasource_id** | **str** | Datasource id of the target table for a cross-source relationship (#1088). | [optional] 
**provenance** | **str** | Provenance note, preserved across a review round-trip (#1088). | [optional] 

## Example

```python
from coa_control_plane_server.models.foreign_key_input import ForeignKeyInput

# TODO update the JSON string below
json = "{}"
# create an instance of ForeignKeyInput from a JSON string
foreign_key_input_instance = ForeignKeyInput.from_json(json)
# print the JSON string representation of the object
print(ForeignKeyInput.to_json())

# convert the object into a dict
foreign_key_input_dict = foreign_key_input_instance.to_dict()
# create an instance of ForeignKeyInput from a dict
foreign_key_input_from_dict = ForeignKeyInput.from_dict(foreign_key_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


