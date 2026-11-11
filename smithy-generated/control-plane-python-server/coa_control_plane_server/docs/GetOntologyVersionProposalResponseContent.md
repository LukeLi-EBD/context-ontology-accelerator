# GetOntologyVersionProposalResponseContent

A proposal plus its version and the diff stored at propose time.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal** | [**OntologyProposal**](OntologyProposal.md) |  | 
**version** | [**OntologyVersion**](OntologyVersion.md) |  | 
**version_status** | [**OntologyVersionStatus**](OntologyVersionStatus.md) |  | 
**diff** | [**OntologyDiff**](OntologyDiff.md) |  | 
**impact** | [**OntologyImpact**](OntologyImpact.md) |  | [optional] 
**current** | [**OntologyPointer**](OntologyPointer.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.get_ontology_version_proposal_response_content import GetOntologyVersionProposalResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOntologyVersionProposalResponseContent from a JSON string
get_ontology_version_proposal_response_content_instance = GetOntologyVersionProposalResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetOntologyVersionProposalResponseContent.to_json())

# convert the object into a dict
get_ontology_version_proposal_response_content_dict = get_ontology_version_proposal_response_content_instance.to_dict()
# create an instance of GetOntologyVersionProposalResponseContent from a dict
get_ontology_version_proposal_response_content_from_dict = GetOntologyVersionProposalResponseContent.from_dict(get_ontology_version_proposal_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


