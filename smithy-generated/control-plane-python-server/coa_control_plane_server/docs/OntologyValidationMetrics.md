# OntologyValidationMetrics

OntoQA-style structural metrics produced by the Tier-2 pass.  Absent members mean the metric could not be computed. This is distinct from zero: `connectedComponents: 0` would claim the graph is empty.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**class_count** | **float** | Declared classes. | [optional] 
**object_property_count** | **float** | Declared object properties. | [optional] 
**datatype_property_count** | **float** | Declared datatype properties. | [optional] 
**relationship_richness** | **float** | Non-inheritance relations divided by total relations. | [optional] 
**attribute_richness** | **float** | Datatype properties divided by classes. | [optional] 
**inheritance_richness** | **float** | Subclass relations divided by classes. | [optional] 
**max_depth** | **float** | Deepest subclass chain. | [optional] 
**connected_components** | **float** | Number of subgraphs not joined by any relation. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_validation_metrics import OntologyValidationMetrics

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyValidationMetrics from a JSON string
ontology_validation_metrics_instance = OntologyValidationMetrics.from_json(json)
# print the JSON string representation of the object
print(OntologyValidationMetrics.to_json())

# convert the object into a dict
ontology_validation_metrics_dict = ontology_validation_metrics_instance.to_dict()
# create an instance of OntologyValidationMetrics from a dict
ontology_validation_metrics_from_dict = OntologyValidationMetrics.from_dict(ontology_validation_metrics_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


