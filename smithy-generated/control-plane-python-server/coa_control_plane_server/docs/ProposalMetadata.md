# ProposalMetadata

Metadata about a proposal.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**datasource_ids** | **List[str]** | Data source IDs this proposal was induced from. | [optional] 
**label** | **str** | Human-readable label for the induction run. | [optional] 
**tables_processed** | **float** | Number of tables processed during induction. | [optional] 
**columns_processed** | **float** | Number of columns processed during induction. | [optional] 
**novel_classes_created** | **float** | Number of novel classes created (not grounded to existing concepts). | [optional] 

## Example

```python
from coa_control_plane_server.models.proposal_metadata import ProposalMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of ProposalMetadata from a JSON string
proposal_metadata_instance = ProposalMetadata.from_json(json)
# print the JSON string representation of the object
print(ProposalMetadata.to_json())

# convert the object into a dict
proposal_metadata_dict = proposal_metadata_instance.to_dict()
# create an instance of ProposalMetadata from a dict
proposal_metadata_from_dict = ProposalMetadata.from_dict(proposal_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


