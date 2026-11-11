# FactUndoReference

The decision that a subsequent undo reverted.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**event_id** | **float** | Event identifier of the undo. | 
**actor** | **str** | Identity that performed the undo. | [optional] 
**reason** | **str** | Why the decision was undone. | [optional] 
**at** | **str** | When the undo was written (ISO-8601). | 

## Example

```python
from coa_control_plane_server.models.fact_undo_reference import FactUndoReference

# TODO update the JSON string below
json = "{}"
# create an instance of FactUndoReference from a JSON string
fact_undo_reference_instance = FactUndoReference.from_json(json)
# print the JSON string representation of the object
print(FactUndoReference.to_json())

# convert the object into a dict
fact_undo_reference_dict = fact_undo_reference_instance.to_dict()
# create an instance of FactUndoReference from a dict
fact_undo_reference_from_dict = FactUndoReference.from_dict(fact_undo_reference_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


