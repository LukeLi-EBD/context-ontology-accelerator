# ListProposalsResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**proposals** | [**List[ProposalSummary]**](ProposalSummary.md) | Proposals matching the query. | 

## Example

```python
from coa_control_plane_server.models.list_proposals_response_content import ListProposalsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListProposalsResponseContent from a JSON string
list_proposals_response_content_instance = ListProposalsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListProposalsResponseContent.to_json())

# convert the object into a dict
list_proposals_response_content_dict = list_proposals_response_content_instance.to_dict()
# create an instance of ListProposalsResponseContent from a dict
list_proposals_response_content_from_dict = ListProposalsResponseContent.from_dict(list_proposals_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


