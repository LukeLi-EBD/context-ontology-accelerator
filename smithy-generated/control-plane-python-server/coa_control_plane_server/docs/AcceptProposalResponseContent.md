# AcceptProposalResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** | UUID v4 identifier. | 
**status** | [**ProposalStatus**](ProposalStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.accept_proposal_response_content import AcceptProposalResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of AcceptProposalResponseContent from a JSON string
accept_proposal_response_content_instance = AcceptProposalResponseContent.from_json(json)
# print the JSON string representation of the object
print(AcceptProposalResponseContent.to_json())

# convert the object into a dict
accept_proposal_response_content_dict = accept_proposal_response_content_instance.to_dict()
# create an instance of AcceptProposalResponseContent from a dict
accept_proposal_response_content_from_dict = AcceptProposalResponseContent.from_dict(accept_proposal_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


