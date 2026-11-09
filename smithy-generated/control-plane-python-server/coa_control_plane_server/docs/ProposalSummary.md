# ProposalSummary

Summary of a proposal (for list views).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** | UUID v4 identifier. | 
**status** | [**ProposalStatus**](ProposalStatus.md) |  | 
**ontology_id** | **str** | Ontology ID this proposal targets. | 
**source_type** | [**InductionSourceType**](InductionSourceType.md) |  | [optional] 
**metadata** | [**ProposalMetadata**](ProposalMetadata.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.proposal_summary import ProposalSummary

# TODO update the JSON string below
json = "{}"
# create an instance of ProposalSummary from a JSON string
proposal_summary_instance = ProposalSummary.from_json(json)
# print the JSON string representation of the object
print(ProposalSummary.to_json())

# convert the object into a dict
proposal_summary_dict = proposal_summary_instance.to_dict()
# create an instance of ProposalSummary from a dict
proposal_summary_from_dict = ProposalSummary.from_dict(proposal_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


