# UpdateSourceColumnMetadataRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**overrides** | [**MetadataOverrides**](MetadataOverrides.md) |  | 

## Example

```python
from coa_control_plane_server.models.update_source_column_metadata_request_content import UpdateSourceColumnMetadataRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateSourceColumnMetadataRequestContent from a JSON string
update_source_column_metadata_request_content_instance = UpdateSourceColumnMetadataRequestContent.from_json(json)
# print the JSON string representation of the object
print(UpdateSourceColumnMetadataRequestContent.to_json())

# convert the object into a dict
update_source_column_metadata_request_content_dict = update_source_column_metadata_request_content_instance.to_dict()
# create an instance of UpdateSourceColumnMetadataRequestContent from a dict
update_source_column_metadata_request_content_from_dict = UpdateSourceColumnMetadataRequestContent.from_dict(update_source_column_metadata_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


