# PlatformGrantSummary

A platform-scoped grant record returned in responses, binding a principal to a platform role that applies across all namespaces (no namespaceId or per-namespace data-access scoping).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**grant_id** | **str** | Unique identifier of the platform grant. | 
**principal_type** | [**PrincipalType**](PrincipalType.md) |  | 
**principal_id** | **str** | Identifier of the principal the grant is bound to. | 
**role** | **str** | Name of the platform role assigned to the principal. | 
**granted_by** | **str** | Identifier of the principal that created the grant. | 
**granted_at** | **str** | Timestamp when the grant was created. | 

## Example

```python
from coa_control_plane_server.models.platform_grant_summary import PlatformGrantSummary

# TODO update the JSON string below
json = "{}"
# create an instance of PlatformGrantSummary from a JSON string
platform_grant_summary_instance = PlatformGrantSummary.from_json(json)
# print the JSON string representation of the object
print(PlatformGrantSummary.to_json())

# convert the object into a dict
platform_grant_summary_dict = platform_grant_summary_instance.to_dict()
# create an instance of PlatformGrantSummary from a dict
platform_grant_summary_from_dict = PlatformGrantSummary.from_dict(platform_grant_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


