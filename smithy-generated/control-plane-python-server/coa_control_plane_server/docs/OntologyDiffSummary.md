# OntologyDiffSummary

Structural summary of a diff.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**added_triples** | **float** | Triples added by the target version. | 
**removed_triples** | **float** | Triples removed by the target version. | 
**added_classes** | **List[str]** | Class IRIs added. | 
**removed_classes** | **List[str]** | Class IRIs removed. | 
**added_properties** | **List[str]** | Property IRIs added. | 
**removed_properties** | **List[str]** | Property IRIs removed. | 
**domain_changes** | [**List[OntologyDomainChange]**](OntologyDomainChange.md) | Domain changes per property. | 
**range_changes** | [**List[OntologyDomainChange]**](OntologyDomainChange.md) | Range changes per property. | 
**removed_class_instances** | [**List[OntologyClassInstance]**](OntologyClassInstance.md) | Removed classes with their instance counts. | 

## Example

```python
from coa_control_plane_server.models.ontology_diff_summary import OntologyDiffSummary

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyDiffSummary from a JSON string
ontology_diff_summary_instance = OntologyDiffSummary.from_json(json)
# print the JSON string representation of the object
print(OntologyDiffSummary.to_json())

# convert the object into a dict
ontology_diff_summary_dict = ontology_diff_summary_instance.to_dict()
# create an instance of OntologyDiffSummary from a dict
ontology_diff_summary_from_dict = OntologyDiffSummary.from_dict(ontology_diff_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


