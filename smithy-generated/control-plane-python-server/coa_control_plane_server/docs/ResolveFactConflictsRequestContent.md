# ResolveFactConflictsRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**subject** | **str** | Conflict group subject. Required unless &#x60;action&#x60; is &#x60;batch&#x60;. | [optional] 
**predicate** | **str** | Conflict group predicate. Required unless &#x60;action&#x60; is &#x60;batch&#x60;. | [optional] 
**action** | [**FactConflictAction**](FactConflictAction.md) |  | 
**keep** | **str** | Value to keep (&#x60;batch&#x60; only; &#x60;keep&#x60; takes it from &#x60;keep&#x60; on the console path, which sends the chosen value here too). | [optional] 
**merged_object** | **str** | Value that replaces the conflicting ones (&#x60;merge&#x60;). | [optional] 
**merged_object_kind** | **str** | &#x60;iri&#x60; (default) or &#x60;literal&#x60;. | [optional] 
**graph** | **str** | Graph for the merged fact; defaults to the group&#39;s graph. | [optional] 
**source_document_id** | **str** | Scope by source document (&#x60;batch&#x60;). | [optional] 
**dry_run** | **bool** | Preview only (&#x60;batch&#x60;); defaults to true. | [optional] 
**actor** | **str** | Identity recorded on the audit event; defaults to &#x60;operator&#x60;. | [optional] 
**reason** | **str** | Why the decision was taken. | [optional] 

## Example

```python
from coa_control_plane_server.models.resolve_fact_conflicts_request_content import ResolveFactConflictsRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ResolveFactConflictsRequestContent from a JSON string
resolve_fact_conflicts_request_content_instance = ResolveFactConflictsRequestContent.from_json(json)
# print the JSON string representation of the object
print(ResolveFactConflictsRequestContent.to_json())

# convert the object into a dict
resolve_fact_conflicts_request_content_dict = resolve_fact_conflicts_request_content_instance.to_dict()
# create an instance of ResolveFactConflictsRequestContent from a dict
resolve_fact_conflicts_request_content_from_dict = ResolveFactConflictsRequestContent.from_dict(resolve_fact_conflicts_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


