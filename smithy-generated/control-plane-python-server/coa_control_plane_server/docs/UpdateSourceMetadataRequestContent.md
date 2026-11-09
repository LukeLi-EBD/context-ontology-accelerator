# UpdateSourceMetadataRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Human-readable display name. Allows spaces and punctuation. 1–128 chars. | [optional] 
**glue_configuration** | [**GlueConfiguration**](GlueConfiguration.md) |  | [optional] 
**jdbc_configuration** | [**JdbcConfiguration**](JdbcConfiguration.md) |  | [optional] 
**custom_connector_configuration** | [**CustomConnectorConfiguration**](CustomConnectorConfiguration.md) |  | [optional] 
**metadata_enrichment_enabled** | **bool** | Whether AI-powered metadata enrichment runs for this source. | [optional] 

## Example

```python
from coa_control_plane_server.models.update_source_metadata_request_content import UpdateSourceMetadataRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateSourceMetadataRequestContent from a JSON string
update_source_metadata_request_content_instance = UpdateSourceMetadataRequestContent.from_json(json)
# print the JSON string representation of the object
print(UpdateSourceMetadataRequestContent.to_json())

# convert the object into a dict
update_source_metadata_request_content_dict = update_source_metadata_request_content_instance.to_dict()
# create an instance of UpdateSourceMetadataRequestContent from a dict
update_source_metadata_request_content_from_dict = UpdateSourceMetadataRequestContent.from_dict(update_source_metadata_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


