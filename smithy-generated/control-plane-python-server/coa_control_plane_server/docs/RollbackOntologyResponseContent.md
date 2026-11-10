# RollbackOntologyResponseContent

Result of `RollbackOntology`; a plan-only call fills the plan view, a real rollback fills the version view.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ok** | **bool** | Always true on a successful real rollback; absent on a plan. | [optional] 
**mode** | [**OntologyRollbackMode**](OntologyRollbackMode.md) |  | [optional] 
**target** | [**OntologyVersion**](OntologyVersion.md) |  | [optional] 
**replaced_version** | [**OntologyVersion**](OntologyVersion.md) |  | [optional] 
**target_version_id** | **str** | Identifier of the target version. | [optional] 
**target_triples** | **float** | Triple count of the target version. | [optional] 
**replaced_version_id** | **str** | Version the pointer replaced. | [optional] 
**id** | **str** | Kernel alias of the published version. | [optional] 
**published_version** | **str** | Contract name of the published version, added by the bridge. | [optional] 
**rollback_of** | **str** | For &#x60;NEW_VERSION&#x60;, the version that was copied. | [optional] 
**semver** | **str** | Semver of the resulting version. | [optional] 
**status** | [**OntologyVersionStatus**](OntologyVersionStatus.md) |  | [optional] 
**graph** | **str** | Graph IRI of the resulting version. | [optional] 
**content_hash** | **str** | Canonical hash of the resulting version. | [optional] 
**triples** | **float** | Triples of the resulting version. | [optional] 
**previous** | **str** | Previous pointer value. | [optional] 
**would_change_pointer** | **bool** | Plan verdict: true when the pointer would move. | [optional] 
**unchanged** | **bool** | True when the pointer already selected the target. | [optional] 
**published_by** | **str** | Who rolled back. | [optional] 
**published_at** | **str** | Publish time of the resulting version (ISO-8601). | [optional] 
**rolled_back_at** | **str** | Rollback time (ISO-8601). | [optional] 
**rolled_back_by** | **str** | Who rolled back. | [optional] 
**reason** | **str** | Reason recorded on the rollback. | [optional] 
**blockers** | [**List[PublishBlocker]**](PublishBlocker.md) | Reasons a rollback would fail. | [optional] 

## Example

```python
from coa_control_plane_server.models.rollback_ontology_response_content import RollbackOntologyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RollbackOntologyResponseContent from a JSON string
rollback_ontology_response_content_instance = RollbackOntologyResponseContent.from_json(json)
# print the JSON string representation of the object
print(RollbackOntologyResponseContent.to_json())

# convert the object into a dict
rollback_ontology_response_content_dict = rollback_ontology_response_content_instance.to_dict()
# create an instance of RollbackOntologyResponseContent from a dict
rollback_ontology_response_content_from_dict = RollbackOntologyResponseContent.from_dict(rollback_ontology_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


