# UpdateProposalRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** | UUID v4 identifier. | 
**ontology_turtle** | **str** | Revised OWL ontology in Turtle format. | [optional] 
**r2rml_turtle** | **str** | Revised R2RML mappings in Turtle format. | [optional] 
**grounding_overrides** | **Dict[str, str]** | Source-table grounding choices. Values are candidate ontology class URIs. | [optional] 
**novel_tables** | **List[str]** | Source tables whose grounding should be cleared so they remain novel, keyed like groundingOverrides. Kept separate from groundingOverrides because OpenAPI map values cannot faithfully preserve Smithy sparse-map nulls. | [optional] 
**ontology_uploaded** | **bool** | Set true when the revised OWL ontology was uploaded directly to S3 via a presigned PUT (see GetProposalUploadUrls) instead of being sent inline in &#x60;ontologyTurtle&#x60; — for large proposals exceeding the API payload cap. Defaults to false (inline). | [optional] 
**r2rml_uploaded** | **bool** | Set true when the revised R2RML was uploaded via presigned PUT instead of inline &#x60;r2rmlTurtle&#x60;. Defaults to false (inline). | [optional] 
**upload_revision_id** | **str** | Immutable revision returned by GetProposalUploadUrls. Required when either uploaded flag is true so an upload cannot overwrite the proposal&#39;s currently active artifacts before validation succeeds. | [optional] 

## Example

```python
from coa_control_plane_server.models.update_proposal_request_content import UpdateProposalRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateProposalRequestContent from a JSON string
update_proposal_request_content_instance = UpdateProposalRequestContent.from_json(json)
# print the JSON string representation of the object
print(UpdateProposalRequestContent.to_json())

# convert the object into a dict
update_proposal_request_content_dict = update_proposal_request_content_instance.to_dict()
# create an instance of UpdateProposalRequestContent from a dict
update_proposal_request_content_from_dict = UpdateProposalRequestContent.from_dict(update_proposal_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


