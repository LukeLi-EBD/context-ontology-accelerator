# ReasoningStage

One stage of a materialization run. Only the members the stage produces are set: `rdfs`/`owl` report triples added, `shacl` reports the gate.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**triples** | **float** | Triples this stage added to the inferred graph. | [optional] 
**conforms** | **bool** | True when the SHACL gate ran and found no violations. | [optional] 
**violations** | **float** | Violations found by the SHACL gate. | [optional] 
**ms** | **float** | Wall time for this stage. | [optional] 

## Example

```python
from coa_control_plane_server.models.reasoning_stage import ReasoningStage

# TODO update the JSON string below
json = "{}"
# create an instance of ReasoningStage from a JSON string
reasoning_stage_instance = ReasoningStage.from_json(json)
# print the JSON string representation of the object
print(ReasoningStage.to_json())

# convert the object into a dict
reasoning_stage_dict = reasoning_stage_instance.to_dict()
# create an instance of ReasoningStage from a dict
reasoning_stage_from_dict = ReasoningStage.from_dict(reasoning_stage_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


