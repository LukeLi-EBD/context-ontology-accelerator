# UndoFactConflictResolutionResponseContent

Result of undoing an adjudication.  `keep` and `keep_both` undo restore the retired rows and return them under `restoredFactIds`; `merge` undo removes the merged row and restores the originals under `restoredFactIds`. `dryRun` fills the same members without writing anything.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dry_run** | **bool** | True when the call only previewed the undo. | 
**event_id** | **float** | Event identifier written by the undo; absent on a dry run. | [optional] 
**subject** | **str** | Subject IRI of the undone group. | 
**predicate** | **str** | Predicate IRI of the undone group. | 
**undone_action** | **str** | Action that was undone. | 
**restored_fact_ids** | **List[str]** | Rows restored by the undo. | [optional] 
**merged_fact_id** | **str** | Merged row removed by the undo (&#x60;merge&#x60; only). | [optional] 
**values** | **List[str]** | Active values after the undo. | [optional] 
**conflict** | **bool** | True when the group conflicts again after the undo. | [optional] 

## Example

```python
from coa_control_plane_server.models.undo_fact_conflict_resolution_response_content import UndoFactConflictResolutionResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of UndoFactConflictResolutionResponseContent from a JSON string
undo_fact_conflict_resolution_response_content_instance = UndoFactConflictResolutionResponseContent.from_json(json)
# print the JSON string representation of the object
print(UndoFactConflictResolutionResponseContent.to_json())

# convert the object into a dict
undo_fact_conflict_resolution_response_content_dict = undo_fact_conflict_resolution_response_content_instance.to_dict()
# create an instance of UndoFactConflictResolutionResponseContent from a dict
undo_fact_conflict_resolution_response_content_from_dict = UndoFactConflictResolutionResponseContent.from_dict(undo_fact_conflict_resolution_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


