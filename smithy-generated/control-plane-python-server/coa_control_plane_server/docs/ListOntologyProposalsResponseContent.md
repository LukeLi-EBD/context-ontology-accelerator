# ListOntologyProposalsResponseContent

Page of proposals for one ontology.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[OntologyProposal]**](OntologyProposal.md) | Proposals in creation order (newest first). | 
**count** | **float** | Number of proposals after filtering. | 
**returned** | **float** | Number of proposals actually returned. | 
**current** | [**OntologyPointer**](OntologyPointer.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.list_ontology_proposals_response_content import ListOntologyProposalsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListOntologyProposalsResponseContent from a JSON string
list_ontology_proposals_response_content_instance = ListOntologyProposalsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListOntologyProposalsResponseContent.to_json())

# convert the object into a dict
list_ontology_proposals_response_content_dict = list_ontology_proposals_response_content_instance.to_dict()
# create an instance of ListOntologyProposalsResponseContent from a dict
list_ontology_proposals_response_content_from_dict = ListOntologyProposalsResponseContent.from_dict(list_ontology_proposals_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


