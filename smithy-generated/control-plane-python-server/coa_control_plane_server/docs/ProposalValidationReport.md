# ProposalValidationReport

Aggregated validation report.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | UUID v4 identifier. | 
**proposal_id** | **str** | UUID v4 identifier. | 
**passed** | **bool** | Whether the proposal passed validation (no blocking findings). | 
**findings** | [**List[ProposalValidationFinding]**](ProposalValidationFinding.md) | All findings produced across the validation tiers. | 
**tiers_run** | [**List[ProposalValidationTier]**](ProposalValidationTier.md) | Validation tiers that were run. | 
**created_at** | **str** | Timestamp when the validation report was created. | 

## Example

```python
from coa_control_plane_server.models.proposal_validation_report import ProposalValidationReport

# TODO update the JSON string below
json = "{}"
# create an instance of ProposalValidationReport from a JSON string
proposal_validation_report_instance = ProposalValidationReport.from_json(json)
# print the JSON string representation of the object
print(ProposalValidationReport.to_json())

# convert the object into a dict
proposal_validation_report_dict = proposal_validation_report_instance.to_dict()
# create an instance of ProposalValidationReport from a dict
proposal_validation_report_from_dict = ProposalValidationReport.from_dict(proposal_validation_report_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


