# OntologyImpactProperty

One affected property.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Property IRI. | 
**label** | **str** | Display label; the IRI&#39;s local name when the T-Box has no label. | 
**change** | [**OntologyImpactChange**](OntologyImpactChange.md) |  | 
**added_triples** | **float** | Triples added under this property. | 
**removed_triples** | **float** | Triples removed under this property. | 
**domain_changes** | [**List[OntologyDomainChange]**](OntologyDomainChange.md) | &#x60;rdfs:domain&#x60; changes recorded for this property. | 
**range_changes** | [**List[OntologyDomainChange]**](OntologyDomainChange.md) | &#x60;rdfs:range&#x60; changes recorded for this property. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_property import OntologyImpactProperty

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactProperty from a JSON string
ontology_impact_property_instance = OntologyImpactProperty.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactProperty.to_json())

# convert the object into a dict
ontology_impact_property_dict = ontology_impact_property_instance.to_dict()
# create an instance of OntologyImpactProperty from a dict
ontology_impact_property_from_dict = OntologyImpactProperty.from_dict(ontology_impact_property_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


