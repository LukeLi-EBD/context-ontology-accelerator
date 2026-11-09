# ApproveFactCandidateResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fact_id** | **str** | Identifier of the written fact. | 
**status** | [**FactCandidateStatus**](FactCandidateStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.approve_fact_candidate_response_content import ApproveFactCandidateResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ApproveFactCandidateResponseContent from a JSON string
approve_fact_candidate_response_content_instance = ApproveFactCandidateResponseContent.from_json(json)
# print the JSON string representation of the object
print(ApproveFactCandidateResponseContent.to_json())

# convert the object into a dict
approve_fact_candidate_response_content_dict = approve_fact_candidate_response_content_instance.to_dict()
# create an instance of ApproveFactCandidateResponseContent from a dict
approve_fact_candidate_response_content_from_dict = ApproveFactCandidateResponseContent.from_dict(approve_fact_candidate_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


