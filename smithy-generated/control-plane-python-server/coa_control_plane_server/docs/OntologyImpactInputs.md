# OntologyImpactInputs

Versions the analysis read.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_from** | [**OntologyImpactVersionRef**](OntologyImpactVersionRef.md) |  | [optional] 
**to** | [**OntologyImpactVersionRef**](OntologyImpactVersionRef.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact_inputs import OntologyImpactInputs

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactInputs from a JSON string
ontology_impact_inputs_instance = OntologyImpactInputs.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactInputs.to_json())

# convert the object into a dict
ontology_impact_inputs_dict = ontology_impact_inputs_instance.to_dict()
# create an instance of OntologyImpactInputs from a dict
ontology_impact_inputs_from_dict = OntologyImpactInputs.from_dict(ontology_impact_inputs_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


