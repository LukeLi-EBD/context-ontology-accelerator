# UpdateProposalResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** | UUID v4 identifier. | 
**status** | [**ProposalStatus**](ProposalStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.update_proposal_response_content import UpdateProposalResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateProposalResponseContent from a JSON string
update_proposal_response_content_instance = UpdateProposalResponseContent.from_json(json)
# print the JSON string representation of the object
print(UpdateProposalResponseContent.to_json())

# convert the object into a dict
update_proposal_response_content_dict = update_proposal_response_content_instance.to_dict()
# create an instance of UpdateProposalResponseContent from a dict
update_proposal_response_content_from_dict = UpdateProposalResponseContent.from_dict(update_proposal_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


