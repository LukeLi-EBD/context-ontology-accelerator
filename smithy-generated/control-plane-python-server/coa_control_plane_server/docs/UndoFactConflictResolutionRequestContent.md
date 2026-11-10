# UndoFactConflictResolutionRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**event_id** | **float** | Adjudication event to undo; alternative to subject + predicate. | [optional] 
**subject** | **str** | Subject of the group; required when &#x60;eventId&#x60; is absent. | [optional] 
**predicate** | **str** | Predicate of the group; required when &#x60;eventId&#x60; is absent. | [optional] 
**actor** | **str** | Identity recorded on the undo event; defaults to &#x60;operator&#x60;. | [optional] 
**reason** | **str** | Why the decision is being undone. | [optional] 
**dry_run** | **bool** | Preview only; defaults to true. | [optional] 

## Example

```python
from coa_control_plane_server.models.undo_fact_conflict_resolution_request_content import UndoFactConflictResolutionRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of UndoFactConflictResolutionRequestContent from a JSON string
undo_fact_conflict_resolution_request_content_instance = UndoFactConflictResolutionRequestContent.from_json(json)
# print the JSON string representation of the object
print(UndoFactConflictResolutionRequestContent.to_json())

# convert the object into a dict
undo_fact_conflict_resolution_request_content_dict = undo_fact_conflict_resolution_request_content_instance.to_dict()
# create an instance of UndoFactConflictResolutionRequestContent from a dict
undo_fact_conflict_resolution_request_content_from_dict = UndoFactConflictResolutionRequestContent.from_dict(undo_fact_conflict_resolution_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


