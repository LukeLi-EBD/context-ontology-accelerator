# GetReasoningStatusResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**available** | **bool** | True only when this deployment has a reasoner configured. | 
**engine** | **str** | Reasoner identifier (for example &#x60;&#x60;elk&#x60;&#x60;); null when none is configured. | [optional] 
**failures** | [**QualityCount**](QualityCount.md) |  | [optional] 
**detail** | **str** | Human-readable explanation of the state above. | [optional] 
**source** | **str** | Where this status came from. | 
**sampled_at** | **str** | When the status was sampled (ISO-8601). | 
**inferred_triples** | **float** | Triples the recorded pointer holds; null until the first run. | [optional] 
**last_job** | [**ReasoningJobSummary**](ReasoningJobSummary.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.get_reasoning_status_response_content import GetReasoningStatusResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetReasoningStatusResponseContent from a JSON string
get_reasoning_status_response_content_instance = GetReasoningStatusResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetReasoningStatusResponseContent.to_json())

# convert the object into a dict
get_reasoning_status_response_content_dict = get_reasoning_status_response_content_instance.to_dict()
# create an instance of GetReasoningStatusResponseContent from a dict
get_reasoning_status_response_content_from_dict = GetReasoningStatusResponseContent.from_dict(get_reasoning_status_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


