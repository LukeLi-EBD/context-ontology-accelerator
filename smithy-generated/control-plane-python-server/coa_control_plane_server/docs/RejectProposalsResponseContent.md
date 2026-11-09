# RejectProposalsResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**rejected** | **float** | Number of proposals rejected. | 

## Example

```python
from coa_control_plane_server.models.reject_proposals_response_content import RejectProposalsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RejectProposalsResponseContent from a JSON string
reject_proposals_response_content_instance = RejectProposalsResponseContent.from_json(json)
# print the JSON string representation of the object
print(RejectProposalsResponseContent.to_json())

# convert the object into a dict
reject_proposals_response_content_dict = reject_proposals_response_content_instance.to_dict()
# create an instance of RejectProposalsResponseContent from a dict
reject_proposals_response_content_from_dict = RejectProposalsResponseContent.from_dict(reject_proposals_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


