# ApproveFactCandidateRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**actor** | **str** | Identity of the approving principal; defaults to the caller. | [optional] 
**fact_overrides** | **Dict[str, str]** | Overrides applied to the fact written when a candidate is approved. Keys are &#x60;subject&#x60;, &#x60;predicate&#x60; and &#x60;object&#x60;; absent keys keep the candidate values. | [optional] 

## Example

```python
from coa_control_plane_server.models.approve_fact_candidate_request_content import ApproveFactCandidateRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ApproveFactCandidateRequestContent from a JSON string
approve_fact_candidate_request_content_instance = ApproveFactCandidateRequestContent.from_json(json)
# print the JSON string representation of the object
print(ApproveFactCandidateRequestContent.to_json())

# convert the object into a dict
approve_fact_candidate_request_content_dict = approve_fact_candidate_request_content_instance.to_dict()
# create an instance of ApproveFactCandidateRequestContent from a dict
approve_fact_candidate_request_content_from_dict = ApproveFactCandidateRequestContent.from_dict(approve_fact_candidate_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


