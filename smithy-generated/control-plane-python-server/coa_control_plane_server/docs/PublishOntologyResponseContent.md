# PublishOntologyResponseContent

Result of `PublishOntology`; a dry run fills the plan view, a real publish fills the version view.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ok** | **bool** | Always true on a successful real publish; absent on a dry run. | [optional] 
**dry_run** | **bool** | True when the call only ran the gates. | [optional] 
**version_id** | **str** | Version being published. | [optional] 
**version_status** | [**OntologyVersionStatus**](OntologyVersionStatus.md) |  | [optional] 
**current_version_id** | **str** | Version the pointer would replace. | [optional] 
**publish_existing** | **bool** | Whether an already registered version was re-activated. | [optional] 
**would_publish** | **bool** | Dry-run verdict: true when the publish would succeed. | [optional] 
**changed** | **bool** | Dry-run verdict: true when the publish would change the pointer. | [optional] 
**id** | **str** | Kernel alias of the published version. | [optional] 
**published_version** | **str** | Contract name of the published version, added by the bridge. | [optional] 
**semver** | **str** | Semver of the published version. | [optional] 
**graph** | **str** | Graph IRI of the published version. | [optional] 
**triple_count** | **float** | Declared triple count. | [optional] 
**triples** | **float** | Triples present in the graph store. | [optional] 
**previous_version_id** | **str** | Version the pointer replaced. | [optional] 
**proposal_id** | **str** | Proposal that authorised the publish. | [optional] 
**published_by** | **str** | Who published. | [optional] 
**published_at** | **str** | Publish time (ISO-8601). | [optional] 
**unchanged** | **bool** | True when the pointer already selected this version. | [optional] 
**idempotent** | **bool** | True when a repeat publish returned the earlier result. | [optional] 
**governed** | **bool** | True when an approved proposal authorised the publish. | [optional] 
**implicit** | **bool** | True when the publish created an implicit proposal. | [optional] 
**implicit_proposal** | **bool** | Kernel alias of &#x60;implicit&#x60;. | [optional] 
**mode** | **str** | &#x60;publish&#x60;, &#x60;activate_existing&#x60;, &#x60;implicit&#x60;, or &#x60;governed&#x60;. | [optional] 
**breaking** | **bool** | True when the diff contains breaking items. | [optional] 
**acknowledge_breaking** | **bool** | Whether the caller acknowledged breaking items. | [optional] 
**impact** | [**OntologyImpact**](OntologyImpact.md) |  | [optional] 
**gates** | **Dict[str, object]** | One gate verdict inside a publish plan. | [optional] 
**blockers** | [**List[PublishBlocker]**](PublishBlocker.md) | Reasons the publish would fail. | [optional] 

## Example

```python
from coa_control_plane_server.models.publish_ontology_response_content import PublishOntologyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of PublishOntologyResponseContent from a JSON string
publish_ontology_response_content_instance = PublishOntologyResponseContent.from_json(json)
# print the JSON string representation of the object
print(PublishOntologyResponseContent.to_json())

# convert the object into a dict
publish_ontology_response_content_dict = publish_ontology_response_content_instance.to_dict()
# create an instance of PublishOntologyResponseContent from a dict
publish_ontology_response_content_from_dict = PublishOntologyResponseContent.from_dict(publish_ontology_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


