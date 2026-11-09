# GetSourceOutput

Full source record returned by GetSource. Uses sourceType as a discriminator — branch on it to access type-specific detail:   DATABASE  → databaseDetails is populated; documentDetails is absent.   DOCUMENTS → documentDetails is populated; databaseDetails is absent.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Unique source identifier. | 
**namespace_id** | **str** | UUID v4 identifier. | 
**name** | **str** | Display name of the source. | 
**source_type** | [**SourceType**](SourceType.md) |  | 
**source_sub_type** | [**SourceSubType**](SourceSubType.md) |  | 
**status** | [**SourceStatus**](SourceStatus.md) |  | 
**created_at** | **float** | Timestamp when the source was created. | 
**updated_at** | **float** | Timestamp when the source was last updated. | [optional] 
**database_details** | [**DatabaseSourceDetail**](DatabaseSourceDetail.md) |  | [optional] 
**document_details** | [**DocumentSourceDetail**](DocumentSourceDetail.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.get_source_output import GetSourceOutput

# TODO update the JSON string below
json = "{}"
# create an instance of GetSourceOutput from a JSON string
get_source_output_instance = GetSourceOutput.from_json(json)
# print the JSON string representation of the object
print(GetSourceOutput.to_json())

# convert the object into a dict
get_source_output_dict = get_source_output_instance.to_dict()
# create an instance of GetSourceOutput from a dict
get_source_output_from_dict = GetSourceOutput.from_dict(get_source_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


