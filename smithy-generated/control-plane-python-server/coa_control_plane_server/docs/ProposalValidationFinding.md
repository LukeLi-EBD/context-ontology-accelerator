# ProposalValidationFinding

One validation finding (e.g. a HermiT inconsistency, OoPS pitfall).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**validator** | **str** | Name of the validator that produced this finding. | 
**tier** | [**ProposalValidationTier**](ProposalValidationTier.md) |  | 
**severity** | [**ProposalValidationSeverity**](ProposalValidationSeverity.md) |  | 
**code** | **str** | Machine-readable code identifying the finding. | 
**message** | **str** | Human-readable description of the finding. | 
**subject** | **str** | Subject IRI the finding refers to (a class/property URI). | [optional] 
**details** | **object** | Structured, finding-specific payload. For MALFORMED_DATATYPE_TOKENS this carries &#x60;offenders&#x60; (a list of &#x60;{subject, predicate, found, canonical}&#x60;), &#x60;count&#x60;, and &#x60;element_count&#x60; so the UI can preview the proposed repair. | [optional] 

## Example

```python
from coa_control_plane_server.models.proposal_validation_finding import ProposalValidationFinding

# TODO update the JSON string below
json = "{}"
# create an instance of ProposalValidationFinding from a JSON string
proposal_validation_finding_instance = ProposalValidationFinding.from_json(json)
# print the JSON string representation of the object
print(ProposalValidationFinding.to_json())

# convert the object into a dict
proposal_validation_finding_dict = proposal_validation_finding_instance.to_dict()
# create an instance of ProposalValidationFinding from a dict
proposal_validation_finding_from_dict = ProposalValidationFinding.from_dict(proposal_validation_finding_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


