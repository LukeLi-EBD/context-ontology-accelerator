# OntologyImpactCounts

Stored diff counts kept on a proposal row.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**added_triples** | **float** | Triples the target version adds. | 
**removed_triples** | **float** | Triples the target version removes. | 
**added_classes** | **float** | Number of class IRIs added. | 
**removed_classes** | **float** | Number of class IRIs removed. | 
**added_properties** | **float** | Number of property IRIs added. | 
**removed_properties** | **float** | Number of property IRIs removed. | 
**domain_changes** | **float** | Number of properties whose &#x60;rdfs:domain&#x60; changed. | 
**range_changes** | **float** | Number of properties whose &#x60;rdfs:range&#x60; changed. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_counts import OntologyImpactCounts

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactCounts from a JSON string
ontology_impact_counts_instance = OntologyImpactCounts.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactCounts.to_json())

# convert the object into a dict
ontology_impact_counts_dict = ontology_impact_counts_instance.to_dict()
# create an instance of OntologyImpactCounts from a dict
ontology_impact_counts_from_dict = OntologyImpactCounts.from_dict(ontology_impact_counts_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


