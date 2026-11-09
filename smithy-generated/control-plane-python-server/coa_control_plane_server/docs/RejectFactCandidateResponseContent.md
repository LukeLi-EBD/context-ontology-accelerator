# RejectFactCandidateResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | [**FactCandidateStatus**](FactCandidateStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.reject_fact_candidate_response_content import RejectFactCandidateResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RejectFactCandidateResponseContent from a JSON string
reject_fact_candidate_response_content_instance = RejectFactCandidateResponseContent.from_json(json)
# print the JSON string representation of the object
print(RejectFactCandidateResponseContent.to_json())

# convert the object into a dict
reject_fact_candidate_response_content_dict = reject_fact_candidate_response_content_instance.to_dict()
# create an instance of RejectFactCandidateResponseContent from a dict
reject_fact_candidate_response_content_from_dict = RejectFactCandidateResponseContent.from_dict(reject_fact_candidate_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


