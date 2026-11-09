# RepairProposalDatatypesResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** | UUID v4 identifier. | 
**repaired_count** | **float** | Number of datatype tokens rewritten (0 when already clean). On a dry run this is the number that WOULD be rewritten. | 
**changes** | [**List[DatatypeRepairChange]**](DatatypeRepairChange.md) | The (before → after) rewrites applied (or, on a dry run, that would be applied), for the preview / post-repair summary. | 
**dry_run** | **bool** | Echoes the request mode: true when this was a non-persisting preview. | [optional] 

## Example

```python
from coa_control_plane_server.models.repair_proposal_datatypes_response_content import RepairProposalDatatypesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RepairProposalDatatypesResponseContent from a JSON string
repair_proposal_datatypes_response_content_instance = RepairProposalDatatypesResponseContent.from_json(json)
# print the JSON string representation of the object
print(RepairProposalDatatypesResponseContent.to_json())

# convert the object into a dict
repair_proposal_datatypes_response_content_dict = repair_proposal_datatypes_response_content_instance.to_dict()
# create an instance of RepairProposalDatatypesResponseContent from a dict
repair_proposal_datatypes_response_content_from_dict = RepairProposalDatatypesResponseContent.from_dict(repair_proposal_datatypes_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


