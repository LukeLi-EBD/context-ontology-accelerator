# OntologyImpactClass

One affected class.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Class IRI. | 
**label** | **str** | Display label; the IRI&#39;s local name when the T-Box has no label. | 
**change** | [**OntologyImpactChange**](OntologyImpactChange.md) |  | 
**added_triples** | **float** | Triples added under this class. | 
**removed_triples** | **float** | Triples removed under this class. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_class import OntologyImpactClass

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactClass from a JSON string
ontology_impact_class_instance = OntologyImpactClass.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactClass.to_json())

# convert the object into a dict
ontology_impact_class_dict = ontology_impact_class_instance.to_dict()
# create an instance of OntologyImpactClass from a dict
ontology_impact_class_from_dict = OntologyImpactClass.from_dict(ontology_impact_class_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


