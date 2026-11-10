# SystemSchemaVersion

Compares the schema version this build expects with the one the database reports.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code_version** | **float** | Highest migration version this build ships. | 
**db_version** | **float** | Highest applied migration version recorded by the database; null when unreadable. | [optional] 
**consistent** | **bool** | True only when both versions are known and equal. | [optional] 
**source** | **str** | Human-readable provenance for the two numbers. | 

## Example

```python
from coa_control_plane_server.models.system_schema_version import SystemSchemaVersion

# TODO update the JSON string below
json = "{}"
# create an instance of SystemSchemaVersion from a JSON string
system_schema_version_instance = SystemSchemaVersion.from_json(json)
# print the JSON string representation of the object
print(SystemSchemaVersion.to_json())

# convert the object into a dict
system_schema_version_dict = system_schema_version_instance.to_dict()
# create an instance of SystemSchemaVersion from a dict
system_schema_version_from_dict = SystemSchemaVersion.from_dict(system_schema_version_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


