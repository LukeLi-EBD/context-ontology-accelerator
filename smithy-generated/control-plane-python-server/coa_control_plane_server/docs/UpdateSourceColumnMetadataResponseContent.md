# UpdateSourceColumnMetadataResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**table_id** | **str** | Identifier of the table containing the column. | 
**column_name** | **str** | Name of the updated column. | 
**review_status** | [**ReviewStatus**](ReviewStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.update_source_column_metadata_response_content import UpdateSourceColumnMetadataResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateSourceColumnMetadataResponseContent from a JSON string
update_source_column_metadata_response_content_instance = UpdateSourceColumnMetadataResponseContent.from_json(json)
# print the JSON string representation of the object
print(UpdateSourceColumnMetadataResponseContent.to_json())

# convert the object into a dict
update_source_column_metadata_response_content_dict = update_source_column_metadata_response_content_instance.to_dict()
# create an instance of UpdateSourceColumnMetadataResponseContent from a dict
update_source_column_metadata_response_content_from_dict = UpdateSourceColumnMetadataResponseContent.from_dict(update_source_column_metadata_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


