# CancelProposalResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** | UUID v4 identifier. | 
**status** | [**ProposalStatus**](ProposalStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.cancel_proposal_response_content import CancelProposalResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of CancelProposalResponseContent from a JSON string
cancel_proposal_response_content_instance = CancelProposalResponseContent.from_json(json)
# print the JSON string representation of the object
print(CancelProposalResponseContent.to_json())

# convert the object into a dict
cancel_proposal_response_content_dict = cancel_proposal_response_content_instance.to_dict()
# create an instance of CancelProposalResponseContent from a dict
cancel_proposal_response_content_from_dict = CancelProposalResponseContent.from_dict(cancel_proposal_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


