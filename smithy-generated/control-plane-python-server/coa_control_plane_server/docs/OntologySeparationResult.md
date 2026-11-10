# OntologySeparationResult

T-Box / PROV zero-mixing check.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ok** | **bool** | True when neither graph carries the other&#39;s nodes. | 
**prov_graph** | **str** | PROV graph IRI. | [optional] 
**tbox_graph** | **str** | T-Box graph IRI. | [optional] 
**prov_triples** | **float** | Triples in the PROV graph. | [optional] 
**tbox_prov_triples** | **float** | PROV triples found in the T-Box graph. | [optional] 
**prov_tbox_triples** | **float** | T-Box triples found in the PROV graph. | [optional] 
**tbox_legacy_prov_predicate_triples** | **float** | Legacy &#x60;prov:&#x60; predicates already present in the T-Box. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_separation_result import OntologySeparationResult

# TODO update the JSON string below
json = "{}"
# create an instance of OntologySeparationResult from a JSON string
ontology_separation_result_instance = OntologySeparationResult.from_json(json)
# print the JSON string representation of the object
print(OntologySeparationResult.to_json())

# convert the object into a dict
ontology_separation_result_dict = ontology_separation_result_instance.to_dict()
# create an instance of OntologySeparationResult from a dict
ontology_separation_result_from_dict = OntologySeparationResult.from_dict(ontology_separation_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


