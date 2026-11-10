# ReviewOntologyProposalResponseContent

Result of `ReviewOntologyProposal`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ok** | **bool** | Always true on a successful review. | [optional] 
**proposal_id** | **str** | Proposal that was reviewed. | 
**version_id** | **str** | Version the proposal targets. | [optional] 
**status** | [**OntologyProposalStatus**](OntologyProposalStatus.md) |  | [optional] 
**version_status** | [**OntologyVersionStatus**](OntologyVersionStatus.md) |  | [optional] 
**approved_by** | **str** | Who approved, when the decision was &#x60;APPROVE&#x60;. | [optional] 
**approved_at** | **str** | Approval time (ISO-8601). | [optional] 
**reviewed_implicitly** | **bool** | True when &#x60;proposed&#x60; was approved without a separate review step. | [optional] 
**rejected_by** | **str** | Who rejected, when the decision was &#x60;REJECT&#x60;. | [optional] 
**rejected_at** | **str** | Rejection time (ISO-8601). | [optional] 
**reason** | **str** | Reason recorded with the decision. | [optional] 
**unchanged** | **bool** | True when the proposal was already in the requested state. | [optional] 

## Example

```python
from coa_control_plane_server.models.review_ontology_proposal_response_content import ReviewOntologyProposalResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ReviewOntologyProposalResponseContent from a JSON string
review_ontology_proposal_response_content_instance = ReviewOntologyProposalResponseContent.from_json(json)
# print the JSON string representation of the object
print(ReviewOntologyProposalResponseContent.to_json())

# convert the object into a dict
review_ontology_proposal_response_content_dict = review_ontology_proposal_response_content_instance.to_dict()
# create an instance of ReviewOntologyProposalResponseContent from a dict
review_ontology_proposal_response_content_from_dict = ReviewOntologyProposalResponseContent.from_dict(review_ontology_proposal_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


