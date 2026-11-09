# CompileConstraintsResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** | UUID v4 identifier. | 
**shapes_turtle** | **str** | Compiled SHACL shapes in Turtle format. | 

## Example

```python
from coa_control_plane_server.models.compile_constraints_response_content import CompileConstraintsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of CompileConstraintsResponseContent from a JSON string
compile_constraints_response_content_instance = CompileConstraintsResponseContent.from_json(json)
# print the JSON string representation of the object
print(CompileConstraintsResponseContent.to_json())

# convert the object into a dict
compile_constraints_response_content_dict = compile_constraints_response_content_instance.to_dict()
# create an instance of CompileConstraintsResponseContent from a dict
compile_constraints_response_content_from_dict = CompileConstraintsResponseContent.from_dict(compile_constraints_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


