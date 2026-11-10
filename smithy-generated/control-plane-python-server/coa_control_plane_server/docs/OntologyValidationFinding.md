# OntologyValidationFinding

One validation finding.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**validator** | **str** | Validator that produced the finding, e.g. &#x60;shacl&#x60; or &#x60;structural&#x60;. | 
**tier** | [**OntologyValidationTier**](OntologyValidationTier.md) |  | 
**severity** | [**OntologyValidationSeverity**](OntologyValidationSeverity.md) |  | 
**code** | **str** | Machine-readable finding code. | 
**message** | **str** | Human-readable description. | 
**subject** | **str** | URI of the offending element, when the finding names one. | [optional] 
**details** | **object** | Validator-specific detail (SHACL path, metric values). Shape is not pinned because it varies per validator. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_validation_finding import OntologyValidationFinding

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyValidationFinding from a JSON string
ontology_validation_finding_instance = OntologyValidationFinding.from_json(json)
# print the JSON string representation of the object
print(OntologyValidationFinding.to_json())

# convert the object into a dict
ontology_validation_finding_dict = ontology_validation_finding_instance.to_dict()
# create an instance of OntologyValidationFinding from a dict
ontology_validation_finding_from_dict = OntologyValidationFinding.from_dict(ontology_validation_finding_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


