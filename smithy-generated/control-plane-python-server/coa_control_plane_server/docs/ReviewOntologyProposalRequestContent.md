# ReviewOntologyProposalRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**decision** | [**OntologyProposalDecision**](OntologyProposalDecision.md) |  | 
**comment** | **str** | Reviewer comment recorded with the decision. | [optional] 
**actor** | **str** | Who reviews. | [optional] 

## Example

```python
from coa_control_plane_server.models.review_ontology_proposal_request_content import ReviewOntologyProposalRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ReviewOntologyProposalRequestContent from a JSON string
review_ontology_proposal_request_content_instance = ReviewOntologyProposalRequestContent.from_json(json)
# print the JSON string representation of the object
print(ReviewOntologyProposalRequestContent.to_json())

# convert the object into a dict
review_ontology_proposal_request_content_dict = review_ontology_proposal_request_content_instance.to_dict()
# create an instance of ReviewOntologyProposalRequestContent from a dict
review_ontology_proposal_request_content_from_dict = ReviewOntologyProposalRequestContent.from_dict(review_ontology_proposal_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


