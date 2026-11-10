# OntologyImpactAffected

What the change affects, as computed at read time.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**classes** | [**List[OntologyImpactClass]**](OntologyImpactClass.md) | Affected classes. | 
**properties** | [**List[OntologyImpactProperty]**](OntologyImpactProperty.md) | Affected properties. | 
**instances** | [**OntologyImpactInstances**](OntologyImpactInstances.md) |  | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_affected import OntologyImpactAffected

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactAffected from a JSON string
ontology_impact_affected_instance = OntologyImpactAffected.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactAffected.to_json())

# convert the object into a dict
ontology_impact_affected_dict = ontology_impact_affected_instance.to_dict()
# create an instance of OntologyImpactAffected from a dict
ontology_impact_affected_from_dict = OntologyImpactAffected.from_dict(ontology_impact_affected_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


