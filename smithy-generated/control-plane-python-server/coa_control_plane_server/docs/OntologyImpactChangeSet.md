# OntologyImpactChangeSet

The change set the analysis was computed from.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**counts** | [**OntologyImpactCounts**](OntologyImpactCounts.md) |  | 
**added_classes** | **List[str]** | Class IRIs added by the target version. | 
**removed_classes** | **List[str]** | Class IRIs removed by the target version. | 
**added_properties** | **List[str]** | Property IRIs added by the target version. | 
**removed_properties** | **List[str]** | Property IRIs removed by the target version. | 
**domain_changes** | [**List[OntologyDomainChange]**](OntologyDomainChange.md) | Domain changes per property. | 
**range_changes** | [**List[OntologyDomainChange]**](OntologyDomainChange.md) | Range changes per property. | 
**breaking** | **bool** | True when at least one breaking item exists. | 
**breaking_items** | [**List[OntologyBreakingItem]**](OntologyBreakingItem.md) | Elements that make the change breaking. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_change_set import OntologyImpactChangeSet

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactChangeSet from a JSON string
ontology_impact_change_set_instance = OntologyImpactChangeSet.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactChangeSet.to_json())

# convert the object into a dict
ontology_impact_change_set_dict = ontology_impact_change_set_instance.to_dict()
# create an instance of OntologyImpactChangeSet from a dict
ontology_impact_change_set_from_dict = OntologyImpactChangeSet.from_dict(ontology_impact_change_set_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


