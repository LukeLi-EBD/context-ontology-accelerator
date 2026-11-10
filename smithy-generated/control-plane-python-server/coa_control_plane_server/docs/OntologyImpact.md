# OntologyImpact

Impact of a proposal.  The counts are written when the proposal is filed. `analysis` and `analysisError` are mutually exclusive: exactly one of them is present on every read, so a caller can always tell \"analysed\" from \"analysis failed\".

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**added_triples** | **float** | Triples the target version adds. | [optional] 
**removed_triples** | **float** | Triples the target version removes. | [optional] 
**added_classes** | **float** | Number of class IRIs added. | [optional] 
**removed_classes** | **float** | Number of class IRIs removed. | [optional] 
**added_properties** | **float** | Number of property IRIs added. | [optional] 
**removed_properties** | **float** | Number of property IRIs removed. | [optional] 
**domain_changes** | **float** | Number of properties whose &#x60;rdfs:domain&#x60; changed. | [optional] 
**range_changes** | **float** | Number of properties whose &#x60;rdfs:range&#x60; changed. | [optional] 
**removed_class_instances** | **float** | Total instances belonging to removed classes. | [optional] 
**breaking_items** | **float** | Number of breaking items recorded in the diff. | [optional] 
**analysis** | [**OntologyImpactAnalysis**](OntologyImpactAnalysis.md) |  | [optional] 
**analysis_error** | [**OntologyImpactError**](OntologyImpactError.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact import OntologyImpact

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpact from a JSON string
ontology_impact_instance = OntologyImpact.from_json(json)
# print the JSON string representation of the object
print(OntologyImpact.to_json())

# convert the object into a dict
ontology_impact_dict = ontology_impact_instance.to_dict()
# create an instance of OntologyImpact from a dict
ontology_impact_from_dict = OntologyImpact.from_dict(ontology_impact_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


