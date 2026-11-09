# RescanSourceRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**confirm_discard_open_review** | **bool** | Acknowledge that starting this re-scan discards an open re-scan review. Required only when the source is in RESCAN_REVIEW: a fresh re-scan re-diffs against the last APPROVED state, so any review decisions or edits made inside the open review window are lost. Omitting it in that state returns 409 rather than silently discarding the review. Ignored from every other status, where a re-scan discards nothing. | [optional] 
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original result instead of starting another scan; reusing the token with different parameters is rejected with ConflictError (409). | [optional] 

## Example

```python
from coa_control_plane_server.models.rescan_source_request_content import RescanSourceRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RescanSourceRequestContent from a JSON string
rescan_source_request_content_instance = RescanSourceRequestContent.from_json(json)
# print the JSON string representation of the object
print(RescanSourceRequestContent.to_json())

# convert the object into a dict
rescan_source_request_content_dict = rescan_source_request_content_instance.to_dict()
# create an instance of RescanSourceRequestContent from a dict
rescan_source_request_content_from_dict = RescanSourceRequestContent.from_dict(rescan_source_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


