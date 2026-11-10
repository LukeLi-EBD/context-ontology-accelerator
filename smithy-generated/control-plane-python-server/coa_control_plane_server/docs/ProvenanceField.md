# ProvenanceField

One field with its three-state evidence badge.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_property** | **str** | Property IRI. | 
**label** | **str** | Property label. | 
**values** | [**List[EntityTerm]**](EntityTerm.md) | Values asserted for the property. | 
**value_text** | **str** | Lexical form of the first literal value. | [optional] 
**asserted** | **bool** | True when the triple is asserted in the A-Box. | 
**inferred_only** | **bool** | True when the triple exists only in the inferred graph. | 
**badge** | [**EntityBadge**](EntityBadge.md) |  | 
**has_source_ref** | **bool** | True when a source reference resolves the value. | 
**has_prov** | **bool** | True when a PROV activity or source reference backs the value. | 
**links** | [**List[ProvenanceLink]**](ProvenanceLink.md) | Resolved evidence links. | 

## Example

```python
from coa_control_plane_server.models.provenance_field import ProvenanceField

# TODO update the JSON string below
json = "{}"
# create an instance of ProvenanceField from a JSON string
provenance_field_instance = ProvenanceField.from_json(json)
# print the JSON string representation of the object
print(ProvenanceField.to_json())

# convert the object into a dict
provenance_field_dict = provenance_field_instance.to_dict()
# create an instance of ProvenanceField from a dict
provenance_field_from_dict = ProvenanceField.from_dict(provenance_field_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


