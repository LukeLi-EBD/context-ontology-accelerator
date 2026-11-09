# CreateGrantRequest

The request body for creating a namespace-scoped grant, binding a principal to a role and optionally scoping data access via a table allowlist, column denylist, and allowed-metrics list.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**principal_type** | [**PrincipalType**](PrincipalType.md) |  | 
**principal_id** | **str** | Identifier of the principal to bind to the role. | 
**role** | **str** | Name of the role to assign to the principal. | 
**table_allowlist** | **List[str]** | Optional list of tables to restrict data access to. | [optional] 
**column_denylist** | **Dict[str, List[str]]** |  | [optional] 
**allowed_metrics** | **List[str]** | Optional list of metrics to permit access to. | [optional] 
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original result instead of creating a duplicate; reusing the token with different parameters is rejected with ConflictError (409). | [optional] 

## Example

```python
from coa_control_plane_server.models.create_grant_request import CreateGrantRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateGrantRequest from a JSON string
create_grant_request_instance = CreateGrantRequest.from_json(json)
# print the JSON string representation of the object
print(CreateGrantRequest.to_json())

# convert the object into a dict
create_grant_request_dict = create_grant_request_instance.to_dict()
# create an instance of CreateGrantRequest from a dict
create_grant_request_from_dict = CreateGrantRequest.from_dict(create_grant_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


