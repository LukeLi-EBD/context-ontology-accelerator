# ValidationWarning

Validation warning returned alongside successful create/update.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_field** | **str** | Name of the field the warning applies to. | 
**message** | **str** | Human-readable description of the warning. | 
**severity** | [**WarningSeverity**](WarningSeverity.md) |  | 

## Example

```python
from coa_control_plane_server.models.validation_warning import ValidationWarning

# TODO update the JSON string below
json = "{}"
# create an instance of ValidationWarning from a JSON string
validation_warning_instance = ValidationWarning.from_json(json)
# print the JSON string representation of the object
print(ValidationWarning.to_json())

# convert the object into a dict
validation_warning_dict = validation_warning_instance.to_dict()
# create an instance of ValidationWarning from a dict
validation_warning_from_dict = ValidationWarning.from_dict(validation_warning_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


