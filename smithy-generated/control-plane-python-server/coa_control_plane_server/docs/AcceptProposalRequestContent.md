# AcceptProposalRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ontology_id** | **str** | Target ontology ID to merge into. If omitted, uses the proposal&#39;s own ontology ID. | [optional] 

## Example

```python
from coa_control_plane_server.models.accept_proposal_request_content import AcceptProposalRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of AcceptProposalRequestContent from a JSON string
accept_proposal_request_content_instance = AcceptProposalRequestContent.from_json(json)
# print the JSON string representation of the object
print(AcceptProposalRequestContent.to_json())

# convert the object into a dict
accept_proposal_request_content_dict = accept_proposal_request_content_instance.to_dict()
# create an instance of AcceptProposalRequestContent from a dict
accept_proposal_request_content_from_dict = AcceptProposalRequestContent.from_dict(accept_proposal_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


