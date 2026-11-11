# ReasoningJobSummary

What the last materialization job left behind.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | Row identifier in &#x60;platform.reasoning_job&#x60;. | 
**state** | **str** | &#x60;queued&#x60;, &#x60;running&#x60;, &#x60;succeeded&#x60;, &#x60;skipped&#x60;, &#x60;failed&#x60; or &#x60;canceled&#x60;. | 
**inferred** | **float** | Triples the run added. | [optional] 
**consistent** | **bool** | Consistency verdict; false fails the run. | [optional] 
**finished_at** | **str** | When the run finished (ISO-8601). | [optional] 
**skipped** | **bool** | True when the run short-circuited because the inputs were unchanged. | [optional] 
**stages** | [**ReasoningStages**](ReasoningStages.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.reasoning_job_summary import ReasoningJobSummary

# TODO update the JSON string below
json = "{}"
# create an instance of ReasoningJobSummary from a JSON string
reasoning_job_summary_instance = ReasoningJobSummary.from_json(json)
# print the JSON string representation of the object
print(ReasoningJobSummary.to_json())

# convert the object into a dict
reasoning_job_summary_dict = reasoning_job_summary_instance.to_dict()
# create an instance of ReasoningJobSummary from a dict
reasoning_job_summary_from_dict = ReasoningJobSummary.from_dict(reasoning_job_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


