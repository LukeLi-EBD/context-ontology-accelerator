# OntologyCoverage

The share of declared classes that the data actually uses.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**class_coverage** | **float** | &#x60;&#x60;classesWithInstances / tbox.classes&#x60;&#x60; in 0..1; 0 when no class is declared. | 
**unlabeled_classes** | **float** | Declared classes without &#x60;&#x60;rdfs:label&#x60;&#x60; or &#x60;&#x60;skos:prefLabel&#x60;&#x60;. | 

## Example

```python
from coa_control_plane_server.models.ontology_coverage import OntologyCoverage

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyCoverage from a JSON string
ontology_coverage_instance = OntologyCoverage.from_json(json)
# print the JSON string representation of the object
print(OntologyCoverage.to_json())

# convert the object into a dict
ontology_coverage_dict = ontology_coverage_instance.to_dict()
# create an instance of OntologyCoverage from a dict
ontology_coverage_from_dict = OntologyCoverage.from_dict(ontology_coverage_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


