# OntologyPropertyRef

One property in the flat property list.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Property IRI. | 
**label** | **str** | Display label. | 
**kind** | **str** | &#x60;ObjectProperty&#x60;, &#x60;DatatypeProperty&#x60;, or &#x60;AnnotationProperty&#x60;. | 

## Example

```python
from coa_control_plane_server.models.ontology_property_ref import OntologyPropertyRef

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyPropertyRef from a JSON string
ontology_property_ref_instance = OntologyPropertyRef.from_json(json)
# print the JSON string representation of the object
print(OntologyPropertyRef.to_json())

# convert the object into a dict
ontology_property_ref_dict = ontology_property_ref_instance.to_dict()
# create an instance of OntologyPropertyRef from a dict
ontology_property_ref_from_dict = OntologyPropertyRef.from_dict(ontology_property_ref_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


