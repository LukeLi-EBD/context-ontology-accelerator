# PrimaryKeyOutput

The primary-key definition reported for a table: its key columns plus the source (e.g. discovered vs. steward-specified) and inference confidence.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**columns** | **List[str]** | Ordered column names composing the primary key. | [optional] 
**source** | **str** | Origin of the key (e.g. discovered vs. steward-specified). | [optional] 
**confidence** | **float** | Inference confidence (0.0-1.0) for AI-inferred keys. | [optional] 

## Example

```python
from coa_control_plane_server.models.primary_key_output import PrimaryKeyOutput

# TODO update the JSON string below
json = "{}"
# create an instance of PrimaryKeyOutput from a JSON string
primary_key_output_instance = PrimaryKeyOutput.from_json(json)
# print the JSON string representation of the object
print(PrimaryKeyOutput.to_json())

# convert the object into a dict
primary_key_output_dict = primary_key_output_instance.to_dict()
# create an instance of PrimaryKeyOutput from a dict
primary_key_output_from_dict = PrimaryKeyOutput.from_dict(primary_key_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


