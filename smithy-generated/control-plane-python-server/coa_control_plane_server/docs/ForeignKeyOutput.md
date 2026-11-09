# ForeignKeyOutput

A foreign-key relationship reported for a table: the local column and the target table/column it references, with the source and inference confidence.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**column** | **str** | Local column holding the foreign-key reference. | [optional] 
**target_table** | **str** | Referenced table. | [optional] 
**target_column** | **str** | Referenced column in the target table. | [optional] 
**source** | **str** | Origin of the key (e.g. discovered vs. steward-specified). | [optional] 
**confidence** | **float** | Inference confidence (0.0-1.0) for AI-inferred keys. | [optional] 
**review_status** | **str** | Steward review state for an inferred relationship (#1088): PENDING_REVIEW, APPROVED, or REJECTED. Empty for authoritative keys (deterministic/steward) and keys predating review. Only APPROVED/authoritative keys reach the ontology. | [optional] 
**target_datasource_id** | **str** | Datasource id of the target table when the relationship crosses a source boundary (#1088). Empty for a within-source key. | [optional] 
**provenance** | **str** | Human-readable note of what an inferred relationship was inferred from, shown to the steward at review time (#1088). | [optional] 

## Example

```python
from coa_control_plane_server.models.foreign_key_output import ForeignKeyOutput

# TODO update the JSON string below
json = "{}"
# create an instance of ForeignKeyOutput from a JSON string
foreign_key_output_instance = ForeignKeyOutput.from_json(json)
# print the JSON string representation of the object
print(ForeignKeyOutput.to_json())

# convert the object into a dict
foreign_key_output_dict = foreign_key_output_instance.to_dict()
# create an instance of ForeignKeyOutput from a dict
foreign_key_output_from_dict = ForeignKeyOutput.from_dict(foreign_key_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


