# StartOntologyValidationRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ontology_id** | **str** | Ontology to validate, resolved through the catalog. | 
**ontology_turtle** | **str** | Inline Turtle that overrides the catalog copy. | [optional] 
**tiers** | [**List[OntologyValidationTier]**](OntologyValidationTier.md) | Tiers to run; all three when absent. | [optional] 
**shacl_shapes_turtle** | **str** | Custom SHACL shapes applied by the Tier-1 pass. | [optional] 
**competency_questions** | **List[str]** | Competency questions the Tier-3 review answers. | [optional] 

## Example

```python
from coa_control_plane_server.models.start_ontology_validation_request_content import StartOntologyValidationRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of StartOntologyValidationRequestContent from a JSON string
start_ontology_validation_request_content_instance = StartOntologyValidationRequestContent.from_json(json)
# print the JSON string representation of the object
print(StartOntologyValidationRequestContent.to_json())

# convert the object into a dict
start_ontology_validation_request_content_dict = start_ontology_validation_request_content_instance.to_dict()
# create an instance of StartOntologyValidationRequestContent from a dict
start_ontology_validation_request_content_from_dict = StartOntologyValidationRequestContent.from_dict(start_ontology_validation_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


