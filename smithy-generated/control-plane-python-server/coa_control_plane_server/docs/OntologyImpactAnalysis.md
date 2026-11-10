# OntologyImpactAnalysis

Read-only change impact analysis of one proposal.  `readOnly` is always true: the analysis runs SPARQL reads and registry queries and writes nothing.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_from** | **str** | Baseline version; absent when the target has no previous version. | [optional] 
**to** | **str** | Target version. | 
**change_set** | [**OntologyImpactChangeSet**](OntologyImpactChangeSet.md) |  | 
**affected** | [**OntologyImpactAffected**](OntologyImpactAffected.md) |  | 
**aggregations** | [**OntologyImpactAggregations**](OntologyImpactAggregations.md) |  | 
**dependencies** | [**OntologyImpactDependencies**](OntologyImpactDependencies.md) |  | 
**verification** | [**OntologyImpactVerification**](OntologyImpactVerification.md) |  | 
**inputs** | [**OntologyImpactInputs**](OntologyImpactInputs.md) |  | [optional] 
**inputs_fingerprint** | **str** | SHA-256 over both content hashes and the diff. | [optional] 
**empty** | **bool** | True when classes, properties, metrics and rules are all empty. | 
**empty_reason** | **str** | Why the analysis is empty. | [optional] 
**computed_at** | **str** | When the analysis ran (ISO-8601). | 
**source** | **str** | Data the analysis was computed from. | 
**read_only** | **bool** | Always true; the analysis never writes. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_analysis import OntologyImpactAnalysis

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactAnalysis from a JSON string
ontology_impact_analysis_instance = OntologyImpactAnalysis.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactAnalysis.to_json())

# convert the object into a dict
ontology_impact_analysis_dict = ontology_impact_analysis_instance.to_dict()
# create an instance of OntologyImpactAnalysis from a dict
ontology_impact_analysis_from_dict = OntologyImpactAnalysis.from_dict(ontology_impact_analysis_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


