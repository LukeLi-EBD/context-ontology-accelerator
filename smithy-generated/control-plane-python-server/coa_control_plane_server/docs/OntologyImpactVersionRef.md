# OntologyImpactVersionRef

One version the analysis read.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version_id** | **str** | Version identifier. | [optional] 
**semver** | **str** | Semantic version. | [optional] 
**content_hash** | **str** | Canonical hash of the version. | [optional] 
**triple_count** | **float** | Declared triple count. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact_version_ref import OntologyImpactVersionRef

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactVersionRef from a JSON string
ontology_impact_version_ref_instance = OntologyImpactVersionRef.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactVersionRef.to_json())

# convert the object into a dict
ontology_impact_version_ref_dict = ontology_impact_version_ref_instance.to_dict()
# create an instance of OntologyImpactVersionRef from a dict
ontology_impact_version_ref_from_dict = OntologyImpactVersionRef.from_dict(ontology_impact_version_ref_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


