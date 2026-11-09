# UpdateSourceTableKeysRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**primary_key** | [**PrimaryKeyInput**](PrimaryKeyInput.md) |  | [optional] 
**foreign_keys** | [**List[ForeignKeyInput]**](ForeignKeyInput.md) | Foreign-key relationships to set for the table. | [optional] 

## Example

```python
from coa_control_plane_server.models.update_source_table_keys_request_content import UpdateSourceTableKeysRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateSourceTableKeysRequestContent from a JSON string
update_source_table_keys_request_content_instance = UpdateSourceTableKeysRequestContent.from_json(json)
# print the JSON string representation of the object
print(UpdateSourceTableKeysRequestContent.to_json())

# convert the object into a dict
update_source_table_keys_request_content_dict = update_source_table_keys_request_content_instance.to_dict()
# create an instance of UpdateSourceTableKeysRequestContent from a dict
update_source_table_keys_request_content_from_dict = UpdateSourceTableKeysRequestContent.from_dict(update_source_table_keys_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


