# CreateSourceOutput

Create source response.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Unique identifier of the newly created source. | 
**status** | [**SourceStatus**](SourceStatus.md) |  | 
**scan_job_id** | **str** | Identifier of the scan job started for the source, if any. | [optional] 
**created_at** | **float** | Timestamp when the source was created. | 

## Example

```python
from coa_control_plane_server.models.create_source_output import CreateSourceOutput

# TODO update the JSON string below
json = "{}"
# create an instance of CreateSourceOutput from a JSON string
create_source_output_instance = CreateSourceOutput.from_json(json)
# print the JSON string representation of the object
print(CreateSourceOutput.to_json())

# convert the object into a dict
create_source_output_dict = create_source_output_instance.to_dict()
# create an instance of CreateSourceOutput from a dict
create_source_output_from_dict = CreateSourceOutput.from_dict(create_source_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


