# OntologyImpactDependencies

Metrics, rules and terms that depend on the affected IRIs.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metrics** | [**List[OntologyImpactMetric]**](OntologyImpactMetric.md) | Metrics whose definitions or bindings mention an affected IRI. | 
**rules** | [**List[OntologyImpactRule]**](OntologyImpactRule.md) | Metric rules that mention an affected IRI, or belong to a hit metric. | 
**terms** | [**List[OntologyImpactTerm]**](OntologyImpactTerm.md) | Dictionary terms whose canonical IRI is affected. | 
**notes** | [**List[OntologyImpactNote]**](OntologyImpactNote.md) | Registries that could not be read; the analysis still returns. | 
**empty** | **bool** | True when no metric and no rule matched. | 
**empty_reason** | **str** | Why nothing matched. | [optional] 
**method** | **str** | How the dependencies were matched. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact_dependencies import OntologyImpactDependencies

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactDependencies from a JSON string
ontology_impact_dependencies_instance = OntologyImpactDependencies.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactDependencies.to_json())

# convert the object into a dict
ontology_impact_dependencies_dict = ontology_impact_dependencies_instance.to_dict()
# create an instance of OntologyImpactDependencies from a dict
ontology_impact_dependencies_from_dict = OntologyImpactDependencies.from_dict(ontology_impact_dependencies_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


