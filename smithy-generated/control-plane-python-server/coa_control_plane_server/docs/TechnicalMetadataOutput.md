# TechnicalMetadataOutput

Technical metadata for a table: column count, partition keys, storage format, and physical location.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**column_count** | **float** | Number of columns in the table. | [optional] 
**partition_keys** | **List[str]** | Names of the table&#39;s partition-key columns. | [optional] 
**format** | **str** | Storage/serialization format. | [optional] 
**location** | **str** | Physical storage location (e.g. S3 URI). | [optional] 

## Example

```python
from coa_control_plane_server.models.technical_metadata_output import TechnicalMetadataOutput

# TODO update the JSON string below
json = "{}"
# create an instance of TechnicalMetadataOutput from a JSON string
technical_metadata_output_instance = TechnicalMetadataOutput.from_json(json)
# print the JSON string representation of the object
print(TechnicalMetadataOutput.to_json())

# convert the object into a dict
technical_metadata_output_dict = technical_metadata_output_instance.to_dict()
# create an instance of TechnicalMetadataOutput from a dict
technical_metadata_output_from_dict = TechnicalMetadataOutput.from_dict(technical_metadata_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


