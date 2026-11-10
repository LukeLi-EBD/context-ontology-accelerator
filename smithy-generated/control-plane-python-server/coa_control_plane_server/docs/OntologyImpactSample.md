# OntologyImpactSample

One class whose instance count was independently recounted.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Class IRI that was sampled. | 
**listed** | **float** | Count reported by the main pass. | 
**recounted** | **float** | Count the independent recount returned. | 
**consistent** | **bool** | True when &#x60;listed&#x60; and &#x60;recounted&#x60; agree. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_sample import OntologyImpactSample

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactSample from a JSON string
ontology_impact_sample_instance = OntologyImpactSample.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactSample.to_json())

# convert the object into a dict
ontology_impact_sample_dict = ontology_impact_sample_instance.to_dict()
# create an instance of OntologyImpactSample from a dict
ontology_impact_sample_from_dict = OntologyImpactSample.from_dict(ontology_impact_sample_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


