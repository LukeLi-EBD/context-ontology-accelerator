# OntologyImpactAggregations

Changed triples grouped by subject class and predicate property.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**by_class** | [**List[OntologyImpactAggregation]**](OntologyImpactAggregation.md) | Changes grouped by subject class. | 
**by_property** | [**List[OntologyImpactAggregation]**](OntologyImpactAggregation.md) | Changes grouped by predicate property. | 
**unclassified** | [**OntologyImpactTripleCount**](OntologyImpactTripleCount.md) |  | 
**empty** | **bool** | True when the two versions have no triple difference. | 
**empty_reason** | **str** | Why &#x60;byClass&#x60;/&#x60;byProperty&#x60; are empty. | [optional] 
**method** | **str** | Aggregation method, e.g. &#x60;SPARQL GROUP BY ?s ?p over (to MINUS from)&#x60;. | [optional] 
**row_limit** | **float** | Row cap applied to the aggregation query. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact_aggregations import OntologyImpactAggregations

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactAggregations from a JSON string
ontology_impact_aggregations_instance = OntologyImpactAggregations.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactAggregations.to_json())

# convert the object into a dict
ontology_impact_aggregations_dict = ontology_impact_aggregations_instance.to_dict()
# create an instance of OntologyImpactAggregations from a dict
ontology_impact_aggregations_from_dict = OntologyImpactAggregations.from_dict(ontology_impact_aggregations_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


