# ListFactCandidatesResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**items** | [**List[FactCandidate]**](FactCandidate.md) | Page of candidates, newest first. | 

## Example

```python
from coa_control_plane_server.models.list_fact_candidates_response_content import ListFactCandidatesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListFactCandidatesResponseContent from a JSON string
list_fact_candidates_response_content_instance = ListFactCandidatesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListFactCandidatesResponseContent.to_json())

# convert the object into a dict
list_fact_candidates_response_content_dict = list_fact_candidates_response_content_instance.to_dict()
# create an instance of ListFactCandidatesResponseContent from a dict
list_fact_candidates_response_content_from_dict = ListFactCandidatesResponseContent.from_dict(list_fact_candidates_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


