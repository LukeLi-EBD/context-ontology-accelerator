# CreateSourceInput

Top-level create request. Exactly one of databaseSource or documentSource must be set, matching the sourceType discriminator.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_type** | [**SourceType**](SourceType.md) |  | 
**database_source** | [**CreateDatabaseSourceInput**](CreateDatabaseSourceInput.md) |  | [optional] 
**document_source** | [**CreateDocumentSourceInput**](CreateDocumentSourceInput.md) |  | [optional] 
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original result instead of creating a duplicate; reusing the token with different parameters is rejected with ConflictError (409). | [optional] 

## Example

```python
from coa_control_plane_server.models.create_source_input import CreateSourceInput

# TODO update the JSON string below
json = "{}"
# create an instance of CreateSourceInput from a JSON string
create_source_input_instance = CreateSourceInput.from_json(json)
# print the JSON string representation of the object
print(CreateSourceInput.to_json())

# convert the object into a dict
create_source_input_dict = create_source_input_instance.to_dict()
# create an instance of CreateSourceInput from a dict
create_source_input_from_dict = CreateSourceInput.from_dict(create_source_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


