# ConformanceWarning

A warning raised when a result row does not conform to the expected SHACL shape, identifying the offending row and shape.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**row** | **float** | Index of the result row that failed conformance. | 
**shape** | **str** | Identifier of the SHACL shape that was violated. | 
**message** | **str** | Human-readable description of the conformance warning. | 

## Example

```python
from coa_data_layer_server.models.conformance_warning import ConformanceWarning

# TODO update the JSON string below
json = "{}"
# create an instance of ConformanceWarning from a JSON string
conformance_warning_instance = ConformanceWarning.from_json(json)
# print the JSON string representation of the object
print(ConformanceWarning.to_json())

# convert the object into a dict
conformance_warning_dict = conformance_warning_instance.to_dict()
# create an instance of ConformanceWarning from a dict
conformance_warning_from_dict = ConformanceWarning.from_dict(conformance_warning_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


