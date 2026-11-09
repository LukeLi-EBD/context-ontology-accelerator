# NamespaceSummary

Condensed view of a namespace as returned in list responses.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**namespace_id** | **str** | UUID v4 identifier. | 
**name** | **str** | Namespace name: 3-64 lowercase alphanumeric or hyphens, must start/end with alphanumeric. | 
**display_name** | **str** | Display name for a namespace. Angle brackets and control characters are rejected. | [optional] 
**status** | [**NamespaceStatus**](NamespaceStatus.md) |  | 
**language** | **str** | Immutable namespace language (canonical BCP 47 tag). Namespaces created before the language field existed report &#x60;en&#x60;. | 
**source_count** | **float** | Number of data sources registered in the namespace. | [optional] 
**created_at** | **str** | Creation timestamp (RFC 3339). | [optional] 
**updated_at** | **str** | Last-update timestamp (RFC 3339). | [optional] 

## Example

```python
from coa_control_plane_server.models.namespace_summary import NamespaceSummary

# TODO update the JSON string below
json = "{}"
# create an instance of NamespaceSummary from a JSON string
namespace_summary_instance = NamespaceSummary.from_json(json)
# print the JSON string representation of the object
print(NamespaceSummary.to_json())

# convert the object into a dict
namespace_summary_dict = namespace_summary_instance.to_dict()
# create an instance of NamespaceSummary from a dict
namespace_summary_from_dict = NamespaceSummary.from_dict(namespace_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


