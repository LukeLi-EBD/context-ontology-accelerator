# OntologyImpactClassInstances

Instance count of one affected class.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Class IRI. | 
**label** | **str** | Display label. | 
**instances** | **float** | Instances of the class across the A-Box graphs.  Not computable when no A-Box graph is configured. Both an absent member and an explicit &#x60;null&#x60; mean exactly that, and the kernel sends &#x60;null&#x60;; neither is &#x60;0&#x60;. A configured A-Box that genuinely holds no instance reports &#x60;0&#x60;. Client generators model this as an optional member (&#x60;?: number&#x60;), so treat &#x60;null&#x60; as a value the field can actually hold at runtime. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact_class_instances import OntologyImpactClassInstances

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactClassInstances from a JSON string
ontology_impact_class_instances_instance = OntologyImpactClassInstances.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactClassInstances.to_json())

# convert the object into a dict
ontology_impact_class_instances_dict = ontology_impact_class_instances_instance.to_dict()
# create an instance of OntologyImpactClassInstances from a dict
ontology_impact_class_instances_from_dict = OntologyImpactClassInstances.from_dict(ontology_impact_class_instances_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


