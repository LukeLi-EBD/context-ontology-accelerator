# ListInductionJobsResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**jobs** | [**List[InductionJobSummary]**](InductionJobSummary.md) | Induction jobs matching the query. | 

## Example

```python
from coa_control_plane_server.models.list_induction_jobs_response_content import ListInductionJobsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListInductionJobsResponseContent from a JSON string
list_induction_jobs_response_content_instance = ListInductionJobsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListInductionJobsResponseContent.to_json())

# convert the object into a dict
list_induction_jobs_response_content_dict = list_induction_jobs_response_content_instance.to_dict()
# create an instance of ListInductionJobsResponseContent from a dict
list_induction_jobs_response_content_from_dict = ListInductionJobsResponseContent.from_dict(list_induction_jobs_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


