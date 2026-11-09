# RejectProposalsRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_ids** | **List[str]** | IDs of the proposals to reject. | 
**reason** | **str** | Reason for rejecting the proposals. | 

## Example

```python
from coa_control_plane_server.models.reject_proposals_request_content import RejectProposalsRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RejectProposalsRequestContent from a JSON string
reject_proposals_request_content_instance = RejectProposalsRequestContent.from_json(json)
# print the JSON string representation of the object
print(RejectProposalsRequestContent.to_json())

# convert the object into a dict
reject_proposals_request_content_dict = reject_proposals_request_content_instance.to_dict()
# create an instance of RejectProposalsRequestContent from a dict
reject_proposals_request_content_from_dict = RejectProposalsRequestContent.from_dict(reject_proposals_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


