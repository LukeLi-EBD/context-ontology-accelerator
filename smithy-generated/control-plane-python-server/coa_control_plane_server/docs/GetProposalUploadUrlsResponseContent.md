# GetProposalUploadUrlsResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**revision_id** | **str** | Revision containing both create-only upload targets. Pass this value to UpdateProposal as uploadRevisionId only after every requested PUT succeeds. | 
**ontology_put_url** | **str** | Create-only S3 PUT URL for the revised OWL ontology Turtle. Send &#x60;If-None-Match: *&#x60;; after 409, 412, or an ambiguous outcome, request a fresh revision rather than reusing this URL. | 
**r2rml_put_url** | **str** | Create-only S3 PUT URL for the revised R2RML Turtle. Send &#x60;If-None-Match: *&#x60;; after 409, 412, or an ambiguous outcome, request a fresh revision rather than reusing this URL. | 

## Example

```python
from coa_control_plane_server.models.get_proposal_upload_urls_response_content import GetProposalUploadUrlsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetProposalUploadUrlsResponseContent from a JSON string
get_proposal_upload_urls_response_content_instance = GetProposalUploadUrlsResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetProposalUploadUrlsResponseContent.to_json())

# convert the object into a dict
get_proposal_upload_urls_response_content_dict = get_proposal_upload_urls_response_content_instance.to_dict()
# create an instance of GetProposalUploadUrlsResponseContent from a dict
get_proposal_upload_urls_response_content_from_dict = GetProposalUploadUrlsResponseContent.from_dict(get_proposal_upload_urls_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


