# OntologyProposal

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
from coa_control_plane_server.models.ontology_proposal import OntologyProposal

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyProposal from a JSON string
ontology_proposal_instance = OntologyProposal.from_json(json)
# print the JSON string representation of the object
print(OntologyProposal.to_json())

# convert the object into a dict
ontology_proposal_dict = ontology_proposal_instance.to_dict()
# create an instance of OntologyProposal from a dict
ontology_proposal_from_dict = OntologyProposal.from_dict(ontology_proposal_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


