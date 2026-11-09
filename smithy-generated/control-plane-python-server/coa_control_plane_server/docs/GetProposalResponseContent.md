# GetProposalResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** | UUID v4 identifier. | 
**status** | [**ProposalStatus**](ProposalStatus.md) |  | 
**ontology_id** | **str** | Ontology ID this proposal targets. | 
**ontology_turtle** | **str** | OWL ontology in Turtle format. Omitted for large proposals that are served out-of-band via &#x60;ontologyUrl&#x60; (a presigned S3 GET URL). | [optional] 
**r2rml_turtle** | **str** | R2RML mappings in Turtle format. Omitted when served via &#x60;r2rmlUrl&#x60;. | [optional] 
**ontology_url** | **str** | Presigned S3 GET URL for the OWL ontology Turtle when it is served out-of-band (proposals exceeding the API payload cap). Null when &#x60;ontologyTurtle&#x60; is inlined. | [optional] 
**r2rml_url** | **str** | Presigned S3 GET URL for the R2RML Turtle when served out-of-band. | [optional] 
**matches_url** | **str** | Presigned S3 GET URL for the grounding-match list (&#x60;matches.json&#x60;) when it is served out-of-band. Null when the match list is small enough to be returned inline. | [optional] 
**constraints_url** | **str** | Presigned S3 GET URL for the SHACL constraint config (&#x60;constraints.ttl&#x60;) when it is served out-of-band. Null when no constraints artifact exists, in which case any small inline &#x60;constraintConfig&#x60; in &#x60;metadata&#x60; is returned instead. | [optional] 
**metadata** | [**ProposalMetadata**](ProposalMetadata.md) |  | [optional] 
**accept_error** | **str** | Error message from the most recent failed accept attempt. Populated when an &#x60;&#x60;accepting&#x60;&#x60; → &#x60;&#x60;pending&#x60;&#x60; rollback occurred; cleared on the next &#x60;&#x60;AcceptProposal&#x60;&#x60; call. | [optional] 

## Example

```python
from coa_control_plane_server.models.get_proposal_response_content import GetProposalResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetProposalResponseContent from a JSON string
get_proposal_response_content_instance = GetProposalResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetProposalResponseContent.to_json())

# convert the object into a dict
get_proposal_response_content_dict = get_proposal_response_content_instance.to_dict()
# create an instance of GetProposalResponseContent from a dict
get_proposal_response_content_from_dict = GetProposalResponseContent.from_dict(get_proposal_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


