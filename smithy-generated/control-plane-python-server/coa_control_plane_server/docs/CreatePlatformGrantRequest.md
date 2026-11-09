# CreatePlatformGrantRequest

The request body for creating a platform-scoped grant, binding a principal to a platform role that applies across all namespaces.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**principal_type** | [**PrincipalType**](PrincipalType.md) |  | 
**principal_id** | **str** | Identifier of the principal to bind to the platform role. | 
**role** | **str** | Name of the platform role to assign to the principal. | 
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original result instead of creating a duplicate; reusing the token with different parameters is rejected with ConflictError (409). | [optional] 

## Example

```python
from coa_control_plane_server.models.create_platform_grant_request import CreatePlatformGrantRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreatePlatformGrantRequest from a JSON string
create_platform_grant_request_instance = CreatePlatformGrantRequest.from_json(json)
# print the JSON string representation of the object
print(CreatePlatformGrantRequest.to_json())

# convert the object into a dict
create_platform_grant_request_dict = create_platform_grant_request_instance.to_dict()
# create an instance of CreatePlatformGrantRequest from a dict
create_platform_grant_request_from_dict = CreatePlatformGrantRequest.from_dict(create_platform_grant_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


