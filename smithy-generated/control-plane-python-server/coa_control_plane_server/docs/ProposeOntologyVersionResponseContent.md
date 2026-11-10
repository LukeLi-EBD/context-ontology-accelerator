# ProposeOntologyVersionResponseContent

One lifecycle proposal.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** | Proposal identifier. | 
**version_id** | **str** | Version the proposal is about. | 
**against_version** | **str** | Version the diff was computed against. | [optional] 
**change_summary** | **str** | What the proposal changes. | [optional] 
**status** | [**OntologyProposalStatus**](OntologyProposalStatus.md) |  | 
**breaking** | **bool** | True when the diff contains breaking items. | 
**acknowledged_breaking** | **bool** | True when a caller acknowledged the breaking items. | [optional] 
**diff** | [**OntologyDiff**](OntologyDiff.md) |  | [optional] 
**impact** | [**OntologyImpact**](OntologyImpact.md) |  | [optional] 
**created_by** | **str** | Who created the proposal. | [optional] 
**created_at** | **str** | Creation time (ISO-8601). | [optional] 
**approved_by** | **str** | Who approved the proposal. | [optional] 
**approved_at** | **str** | Approval time (ISO-8601). | [optional] 
**published_at** | **str** | Publish time of the proposal (ISO-8601). | [optional] 
**version_status** | [**OntologyVersionStatus**](OntologyVersionStatus.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.propose_ontology_version_response_content import ProposeOntologyVersionResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ProposeOntologyVersionResponseContent from a JSON string
propose_ontology_version_response_content_instance = ProposeOntologyVersionResponseContent.from_json(json)
# print the JSON string representation of the object
print(ProposeOntologyVersionResponseContent.to_json())

# convert the object into a dict
propose_ontology_version_response_content_dict = propose_ontology_version_response_content_instance.to_dict()
# create an instance of ProposeOntologyVersionResponseContent from a dict
propose_ontology_version_response_content_from_dict = ProposeOntologyVersionResponseContent.from_dict(propose_ontology_version_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


