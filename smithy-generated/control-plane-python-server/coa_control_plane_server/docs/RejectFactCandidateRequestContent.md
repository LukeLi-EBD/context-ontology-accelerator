# RejectFactCandidateRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**actor** | **str** | Identity of the rejecting principal; defaults to the caller. | [optional] 
**reason** | **str** | Why the candidate was rejected. | 

## Example

```python
from coa_control_plane_server.models.reject_fact_candidate_request_content import RejectFactCandidateRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RejectFactCandidateRequestContent from a JSON string
reject_fact_candidate_request_content_instance = RejectFactCandidateRequestContent.from_json(json)
# print the JSON string representation of the object
print(RejectFactCandidateRequestContent.to_json())

# convert the object into a dict
reject_fact_candidate_request_content_dict = reject_fact_candidate_request_content_instance.to_dict()
# create an instance of RejectFactCandidateRequestContent from a dict
reject_fact_candidate_request_content_from_dict = RejectFactCandidateRequestContent.from_dict(reject_fact_candidate_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


