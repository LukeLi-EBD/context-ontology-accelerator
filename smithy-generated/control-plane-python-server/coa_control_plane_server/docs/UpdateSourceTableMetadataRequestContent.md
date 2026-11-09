# UpdateSourceTableMetadataRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**overrides** | [**MetadataOverrides**](MetadataOverrides.md) |  | 

## Example

```python
from coa_control_plane_server.models.update_source_table_metadata_request_content import UpdateSourceTableMetadataRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateSourceTableMetadataRequestContent from a JSON string
update_source_table_metadata_request_content_instance = UpdateSourceTableMetadataRequestContent.from_json(json)
# print the JSON string representation of the object
print(UpdateSourceTableMetadataRequestContent.to_json())

# convert the object into a dict
update_source_table_metadata_request_content_dict = update_source_table_metadata_request_content_instance.to_dict()
# create an instance of UpdateSourceTableMetadataRequestContent from a dict
update_source_table_metadata_request_content_from_dict = UpdateSourceTableMetadataRequestContent.from_dict(update_source_table_metadata_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


