# OntologyImpactTerm

One dictionary term whose canonical IRI is affected.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**surface** | **str** | Surface form the term is written as. | [optional] 
**canonical** | **str** | Canonical IRI the surface form resolves to. | [optional] 
**lang** | **str** | Language tag, e.g. &#x60;zh&#x60;. | [optional] 
**source** | **str** | Where the term entry came from. | [optional] 
**canonical_label** | **str** | Local name of &#x60;canonical&#x60;, for display. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact_term import OntologyImpactTerm

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactTerm from a JSON string
ontology_impact_term_instance = OntologyImpactTerm.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactTerm.to_json())

# convert the object into a dict
ontology_impact_term_dict = ontology_impact_term_instance.to_dict()
# create an instance of OntologyImpactTerm from a dict
ontology_impact_term_from_dict = OntologyImpactTerm.from_dict(ontology_impact_term_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


