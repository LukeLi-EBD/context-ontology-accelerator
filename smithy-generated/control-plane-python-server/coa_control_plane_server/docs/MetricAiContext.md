# MetricAiContext

AI context for metric discoverability.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**synonyms** | **List[str]** | Alternative names the metric may be referred to by. | [optional] 
**instructions** | **str** | Free-text guidance for how to use or interpret the metric. | [optional] 
**examples** | **List[str]** | Example questions or usages illustrating the metric. | [optional] 

## Example

```python
from coa_control_plane_server.models.metric_ai_context import MetricAiContext

# TODO update the JSON string below
json = "{}"
# create an instance of MetricAiContext from a JSON string
metric_ai_context_instance = MetricAiContext.from_json(json)
# print the JSON string representation of the object
print(MetricAiContext.to_json())

# convert the object into a dict
metric_ai_context_dict = metric_ai_context_instance.to_dict()
# create an instance of MetricAiContext from a dict
metric_ai_context_from_dict = MetricAiContext.from_dict(metric_ai_context_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


