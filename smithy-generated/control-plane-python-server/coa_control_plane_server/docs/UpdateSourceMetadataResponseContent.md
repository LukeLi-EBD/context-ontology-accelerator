# UpdateSourceMetadataResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Identifier of the updated source. | 
**status** | [**SourceStatus**](SourceStatus.md) |  | 
**updated_at** | **float** | Timestamp when the source was last updated. | 

## Example

```python
from coa_control_plane_server.models.update_source_metadata_response_content import UpdateSourceMetadataResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateSourceMetadataResponseContent from a JSON string
update_source_metadata_response_content_instance = UpdateSourceMetadataResponseContent.from_json(json)
# print the JSON string representation of the object
print(UpdateSourceMetadataResponseContent.to_json())

# convert the object into a dict
update_source_metadata_response_content_dict = update_source_metadata_response_content_instance.to_dict()
# create an instance of UpdateSourceMetadataResponseContent from a dict
update_source_metadata_response_content_from_dict = UpdateSourceMetadataResponseContent.from_dict(update_source_metadata_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


