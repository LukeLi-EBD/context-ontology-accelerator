# ValidateProposalRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tiers** | [**List[ProposalValidationTier]**](ProposalValidationTier.md) | Validator tiers to run (defaults to all three tiers if omitted). | [optional] 
**shacl_shapes_turtle** | **str** | Optional SHACL shapes Turtle for tier-1 SHACL validation. | [optional] 
**competency_questions** | **List[str]** | Optional competency-question prompts for tier-3 LLM validators. | [optional] 
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original job handle instead of starting a second validation job; reusing the token with different parameters is rejected with a 409. | [optional] 

## Example

```python
from coa_control_plane_server.models.validate_proposal_request_content import ValidateProposalRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ValidateProposalRequestContent from a JSON string
validate_proposal_request_content_instance = ValidateProposalRequestContent.from_json(json)
# print the JSON string representation of the object
print(ValidateProposalRequestContent.to_json())

# convert the object into a dict
validate_proposal_request_content_dict = validate_proposal_request_content_instance.to_dict()
# create an instance of ValidateProposalRequestContent from a dict
validate_proposal_request_content_from_dict = ValidateProposalRequestContent.from_dict(validate_proposal_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


