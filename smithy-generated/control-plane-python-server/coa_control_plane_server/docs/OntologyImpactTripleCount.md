# OntologyImpactTripleCount

Triple counts that could not be attributed to a class or property.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**added_triples** | **float** | Triples added. | 
**removed_triples** | **float** | Triples removed. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_triple_count import OntologyImpactTripleCount

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactTripleCount from a JSON string
ontology_impact_triple_count_instance = OntologyImpactTripleCount.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactTripleCount.to_json())

# convert the object into a dict
ontology_impact_triple_count_dict = ontology_impact_triple_count_instance.to_dict()
# create an instance of OntologyImpactTripleCount from a dict
ontology_impact_triple_count_from_dict = OntologyImpactTripleCount.from_dict(ontology_impact_triple_count_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


