# UpdateSourceTableMetadataResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**table_id** | **str** | Identifier of the updated table. | 
**review_status** | [**ReviewStatus**](ReviewStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.update_source_table_metadata_response_content import UpdateSourceTableMetadataResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateSourceTableMetadataResponseContent from a JSON string
update_source_table_metadata_response_content_instance = UpdateSourceTableMetadataResponseContent.from_json(json)
# print the JSON string representation of the object
print(UpdateSourceTableMetadataResponseContent.to_json())

# convert the object into a dict
update_source_table_metadata_response_content_dict = update_source_table_metadata_response_content_instance.to_dict()
# create an instance of UpdateSourceTableMetadataResponseContent from a dict
update_source_table_metadata_response_content_from_dict = UpdateSourceTableMetadataResponseContent.from_dict(update_source_table_metadata_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


