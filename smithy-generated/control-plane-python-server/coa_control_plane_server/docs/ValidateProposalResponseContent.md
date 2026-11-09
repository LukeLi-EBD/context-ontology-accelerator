# ValidateProposalResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | UUID v4 identifier. | 
**proposal_id** | **str** | UUID v4 identifier. | 
**status** | [**ProposalValidationJobStatus**](ProposalValidationJobStatus.md) |  | 
**created_at** | **str** | Timestamp when the validation job was created. | 

## Example

```python
from coa_control_plane_server.models.validate_proposal_response_content import ValidateProposalResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ValidateProposalResponseContent from a JSON string
validate_proposal_response_content_instance = ValidateProposalResponseContent.from_json(json)
# print the JSON string representation of the object
print(ValidateProposalResponseContent.to_json())

# convert the object into a dict
validate_proposal_response_content_dict = validate_proposal_response_content_instance.to_dict()
# create an instance of ValidateProposalResponseContent from a dict
validate_proposal_response_content_from_dict = ValidateProposalResponseContent.from_dict(validate_proposal_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


