# RepairProposalDatatypesRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dry_run** | **bool** | When true, preview the repairs (return the change list) without persisting anything or changing the proposal&#39;s status. Defaults false. | [optional] 

## Example

```python
from coa_control_plane_server.models.repair_proposal_datatypes_request_content import RepairProposalDatatypesRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RepairProposalDatatypesRequestContent from a JSON string
repair_proposal_datatypes_request_content_instance = RepairProposalDatatypesRequestContent.from_json(json)
# print the JSON string representation of the object
print(RepairProposalDatatypesRequestContent.to_json())

# convert the object into a dict
repair_proposal_datatypes_request_content_dict = repair_proposal_datatypes_request_content_instance.to_dict()
# create an instance of RepairProposalDatatypesRequestContent from a dict
repair_proposal_datatypes_request_content_from_dict = RepairProposalDatatypesRequestContent.from_dict(repair_proposal_datatypes_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


