# PrimaryKeyInput

Steward-supplied primary key. Replaces the table's primary key; an empty columns list clears it. Stored with source = STEWARD_SPECIFIED.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**columns** | **List[str]** | Column names composing the primary key; empty list clears it. | 

## Example

```python
from coa_control_plane_server.models.primary_key_input import PrimaryKeyInput

# TODO update the JSON string below
json = "{}"
# create an instance of PrimaryKeyInput from a JSON string
primary_key_input_instance = PrimaryKeyInput.from_json(json)
# print the JSON string representation of the object
print(PrimaryKeyInput.to_json())

# convert the object into a dict
primary_key_input_dict = primary_key_input_instance.to_dict()
# create an instance of PrimaryKeyInput from a dict
primary_key_input_from_dict = PrimaryKeyInput.from_dict(primary_key_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


