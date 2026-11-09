# NamespaceDetail

Full detail view of a namespace, including owner, description, and system-managed fields.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**namespace_id** | **str** | UUID v4 identifier. | 
**name** | **str** | Namespace name: 3-64 lowercase alphanumeric or hyphens, must start/end with alphanumeric. | 
**display_name** | **str** | Display name for a namespace. Angle brackets and control characters are rejected. | [optional] 
**description** | **str** | Namespace description. Angle brackets and control characters other than tab and newline are rejected. | [optional] 
**owner** | **str** | Owner email address. The local part allows the RFC 5322 atext characters except # | and backtick (the owner also becomes a grant principalId). Personal information, so marked sensitive to keep it out of generated-client logs. | 
**status** | [**NamespaceStatus**](NamespaceStatus.md) |  | 
**language** | **str** | Immutable namespace language (canonical BCP 47 tag), set at creation. Namespaces created before the language field existed report &#x60;en&#x60;. | 
**data_zone_project_id** | **str** | Amazon DataZone project ID linked to this namespace, when applicable. | [optional] 
**source_count** | **float** | Number of data sources registered in the namespace. | [optional] 
**created_at** | **str** | Creation timestamp (RFC 3339). | 
**updated_at** | **str** | Last-update timestamp (RFC 3339). | [optional] 
**athena_workgroup_name** | **str** | Name of the Athena workgroup created for this namespace (read-only, system-managed). Use this workgroup when querying data sources via Athena federation. Format: &#x60;{resource-prefix}{namespaceId}&#x60;. Null when workgroup provisioning could not be confirmed (e.g., SSM parameter missing) — in that case Athena queries against this namespace&#39;s federated catalogs are not yet supported and a re-creation is required to enable them. | [optional] 
**datasource_external_id** | **str** | STS ExternalId the platform presents when assuming a cross-account role onboarded into this namespace (read-only, system-derived). Format: &#x60;{resource-prefix}{namespaceId}&#x60;, the same scheme as &#x60;athenaWorkgroupName&#x60;.  Any role supplied as &#x60;crossAccountRoleArn&#x60; MUST condition its trust policy on this exact value (&#x60;sts:ExternalId&#x60;). The platform derives it server-side and refuses to assume a role without presenting one, so this is what stops a caller in one namespace from pointing a source at a role onboarded for another. Surface it wherever a cross-account role is configured. | [optional] 
**vkg_health** | [**VkgHealthStatus**](VkgHealthStatus.md) |  | [optional] 
**vkg_health_reason** | **str** | Human-readable explanation for a non-HEALTHY vkgHealth, when known (e.g. \&quot;container health check failing\&quot;, \&quot;no running task\&quot;). Absent when HEALTHY. Coarse by design — the precise container-side cause is in the VKG service /health response and its CloudWatch logs. | [optional] 

## Example

```python
from coa_control_plane_server.models.namespace_detail import NamespaceDetail

# TODO update the JSON string below
json = "{}"
# create an instance of NamespaceDetail from a JSON string
namespace_detail_instance = NamespaceDetail.from_json(json)
# print the JSON string representation of the object
print(NamespaceDetail.to_json())

# convert the object into a dict
namespace_detail_dict = namespace_detail_instance.to_dict()
# create an instance of NamespaceDetail from a dict
namespace_detail_from_dict = NamespaceDetail.from_dict(namespace_detail_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


