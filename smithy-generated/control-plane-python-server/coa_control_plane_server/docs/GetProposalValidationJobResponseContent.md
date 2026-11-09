# GetProposalValidationJobResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | UUID v4 identifier. | 
**proposal_id** | **str** | UUID v4 identifier. | 
**status** | [**ProposalValidationJobStatus**](ProposalValidationJobStatus.md) |  | 
**created_at** | **str** | Timestamp when the validation job was created. | 
**error** | **str** | Error message if status is FAILED. | [optional] 
**report** | [**ProposalValidationReport**](ProposalValidationReport.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.get_proposal_validation_job_response_content import GetProposalValidationJobResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetProposalValidationJobResponseContent from a JSON string
get_proposal_validation_job_response_content_instance = GetProposalValidationJobResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetProposalValidationJobResponseContent.to_json())

# convert the object into a dict
get_proposal_validation_job_response_content_dict = get_proposal_validation_job_response_content_instance.to_dict()
# create an instance of GetProposalValidationJobResponseContent from a dict
get_proposal_validation_job_response_content_from_dict = GetProposalValidationJobResponseContent.from_dict(get_proposal_validation_job_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


