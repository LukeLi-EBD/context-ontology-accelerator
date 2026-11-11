# RollbackOntologyRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**target_version_id** | **str** | Version to restore. | 
**mode** | [**OntologyRollbackMode**](OntologyRollbackMode.md) |  | 
**expected_version_id** | **str** | Optimistic-concurrency guard for &#x60;POINTER_ONLY&#x60;. | [optional] 
**plan_only** | **bool** | Return the plan only; nothing is written. | [optional] 
**actor** | **str** | Who rolls back. | [optional] 
**reason** | **str** | Reason recorded on the rollback. | [optional] 

## Example

```python
from coa_control_plane_server.models.rollback_ontology_request_content import RollbackOntologyRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RollbackOntologyRequestContent from a JSON string
rollback_ontology_request_content_instance = RollbackOntologyRequestContent.from_json(json)
# print the JSON string representation of the object
print(RollbackOntologyRequestContent.to_json())

# convert the object into a dict
rollback_ontology_request_content_dict = rollback_ontology_request_content_instance.to_dict()
# create an instance of RollbackOntologyRequestContent from a dict
rollback_ontology_request_content_from_dict = RollbackOntologyRequestContent.from_dict(rollback_ontology_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


