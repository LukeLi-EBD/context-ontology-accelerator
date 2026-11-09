# OntologyPropertySummary

One property persisted in an ontology's named graph. Object properties carry a class IRI in ``range`` (a relationship); datatype properties carry a datatype IRI (e.g. xsd:string).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | IRI of the property. | 
**label** | **str** | Human-readable label (rdfs:label) of the property. | [optional] 
**domain** | **str** | IRI of the property&#39;s domain class. | [optional] 
**range** | **str** | IRI of the property&#39;s range (a class IRI for object properties, a datatype IRI for datatype properties). | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_property_summary import OntologyPropertySummary

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyPropertySummary from a JSON string
ontology_property_summary_instance = OntologyPropertySummary.from_json(json)
# print the JSON string representation of the object
print(OntologyPropertySummary.to_json())

# convert the object into a dict
ontology_property_summary_dict = ontology_property_summary_instance.to_dict()
# create an instance of OntologyPropertySummary from a dict
ontology_property_summary_from_dict = OntologyPropertySummary.from_dict(ontology_property_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


