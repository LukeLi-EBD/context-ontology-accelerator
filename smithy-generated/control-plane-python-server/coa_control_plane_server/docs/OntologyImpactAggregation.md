# OntologyImpactAggregation

One class or property in the aggregation view.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Class or property IRI. | 
**label** | **str** | Display label. | 
**added_triples** | **float** | Triples added under this IRI. | 
**removed_triples** | **float** | Triples removed under this IRI. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_aggregation import OntologyImpactAggregation

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactAggregation from a JSON string
ontology_impact_aggregation_instance = OntologyImpactAggregation.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactAggregation.to_json())

# convert the object into a dict
ontology_impact_aggregation_dict = ontology_impact_aggregation_instance.to_dict()
# create an instance of OntologyImpactAggregation from a dict
ontology_impact_aggregation_from_dict = OntologyImpactAggregation.from_dict(ontology_impact_aggregation_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


