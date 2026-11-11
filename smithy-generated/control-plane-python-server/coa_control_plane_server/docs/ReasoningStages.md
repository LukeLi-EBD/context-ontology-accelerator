# ReasoningStages

Stages of a materialization run, in execution order.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**rdfs** | [**ReasoningStage**](ReasoningStage.md) |  | [optional] 
**owl** | [**ReasoningStage**](ReasoningStage.md) |  | [optional] 
**shacl** | [**ReasoningStage**](ReasoningStage.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.reasoning_stages import ReasoningStages

# TODO update the JSON string below
json = "{}"
# create an instance of ReasoningStages from a JSON string
reasoning_stages_instance = ReasoningStages.from_json(json)
# print the JSON string representation of the object
print(ReasoningStages.to_json())

# convert the object into a dict
reasoning_stages_dict = reasoning_stages_instance.to_dict()
# create an instance of ReasoningStages from a dict
reasoning_stages_from_dict = ReasoningStages.from_dict(reasoning_stages_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


