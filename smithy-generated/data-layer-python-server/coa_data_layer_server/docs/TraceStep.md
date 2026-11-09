# TraceStep

One step in a query's execution trace, recording what ran, its status, timing, and any tool used or conformance warnings raised.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**step** | **str** | Name of the execution step. | 
**status** | **str** | Status of the step (e.g. success or failure). | 
**duration_ms** | **float** | Duration of the step in milliseconds. | [optional] 
**detail** | **str** | Additional detail about the step. | [optional] 
**tool_used** | **str** | Name of the tool invoked during the step, if any. | [optional] 
**parallel_group** | **str** | Identifier of the parallel group this step ran in, if any. | [optional] 
**wall_ms** | **float** | Wall-clock time for the step in milliseconds. | [optional] 
**conformance_warnings** | [**List[ConformanceWarning]**](ConformanceWarning.md) | Conformance warnings raised during the step. | [optional] 

## Example

```python
from coa_data_layer_server.models.trace_step import TraceStep

# TODO update the JSON string below
json = "{}"
# create an instance of TraceStep from a JSON string
trace_step_instance = TraceStep.from_json(json)
# print the JSON string representation of the object
print(TraceStep.to_json())

# convert the object into a dict
trace_step_dict = trace_step_instance.to_dict()
# create an instance of TraceStep from a dict
trace_step_from_dict = TraceStep.from_dict(trace_step_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


