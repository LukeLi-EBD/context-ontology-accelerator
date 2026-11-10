# GetEntityProvenanceResponseContent

Per-field provenance report for one entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Entity IRI. | 
**label** | **str** | Display label. | 
**fields** | [**List[ProvenanceField]**](ProvenanceField.md) | Fields with evidence badges. | 
**statements** | [**List[ProvenanceField]**](ProvenanceField.md) | Statement view; mirrors &#x60;fields&#x60; for the statement table. | 
**activities** | [**List[ProvenanceActivity]**](ProvenanceActivity.md) | PROV activities related to the entity. | 
**citations** | [**List[ProvenanceCitation]**](ProvenanceCitation.md) | Citations that resolve field values. | 
**summary** | [**ProvenanceSummary**](ProvenanceSummary.md) |  | 
**evidence_badge** | [**EntityBadge**](EntityBadge.md) |  | 
**named_graphs** | **List[str]** | Named graphs that supplied the returned statements. | 
**provenance** | [**EntityProvenance**](EntityProvenance.md) |  | 
**empty** | **bool** | True when the entity has no properties. | 
**empty_reason** | **str** | Why the report is empty, when it is. | [optional] 
**note** | **str** | Fixed note explaining the badge semantics. | 

## Example

```python
from coa_control_plane_server.models.get_entity_provenance_response_content import GetEntityProvenanceResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetEntityProvenanceResponseContent from a JSON string
get_entity_provenance_response_content_instance = GetEntityProvenanceResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetEntityProvenanceResponseContent.to_json())

# convert the object into a dict
get_entity_provenance_response_content_dict = get_entity_provenance_response_content_instance.to_dict()
# create an instance of GetEntityProvenanceResponseContent from a dict
get_entity_provenance_response_content_from_dict = GetEntityProvenanceResponseContent.from_dict(get_entity_provenance_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


