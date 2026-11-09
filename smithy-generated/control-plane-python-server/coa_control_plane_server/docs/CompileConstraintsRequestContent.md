# CompileConstraintsRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**constraint_config** | **object** | Reviewed ConstraintConfig to compile into SHACL. At most 65536 bytes once serialized as JSON; larger configs are rejected with a 400. | 
**custom_turtle** | **str** | Optional custom SHACL Turtle to merge with the compiled shapes. | [optional] 

## Example

```python
from coa_control_plane_server.models.compile_constraints_request_content import CompileConstraintsRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of CompileConstraintsRequestContent from a JSON string
compile_constraints_request_content_instance = CompileConstraintsRequestContent.from_json(json)
# print the JSON string representation of the object
print(CompileConstraintsRequestContent.to_json())

# convert the object into a dict
compile_constraints_request_content_dict = compile_constraints_request_content_instance.to_dict()
# create an instance of CompileConstraintsRequestContent from a dict
compile_constraints_request_content_from_dict = CompileConstraintsRequestContent.from_dict(compile_constraints_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


