# OntologyShaclResult

SHACL outcome recorded by an import.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**shapes_id** | **str** | Identifier of the deployed shapes graph. | [optional] 
**shapes_version** | **str** | Version of the deployed shapes graph. | [optional] 
**conforms** | **bool** | True when the shapes conform; null when no shapes were configured. | [optional] 
**violation_count** | **float** | Number of violations reported by the validator. | [optional] 
**status** | **str** | &#x60;validated&#x60; or &#x60;error&#x60;. | [optional] 
**engine** | **str** | Validator engine, e.g. &#x60;pyshacl&#x60;. | [optional] 
**error** | **str** | Validation error, when &#x60;status&#x60; is &#x60;error&#x60;. | [optional] 
**violations** | **List[object]** | Violations reported by the validator. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_shacl_result import OntologyShaclResult

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyShaclResult from a JSON string
ontology_shacl_result_instance = OntologyShaclResult.from_json(json)
# print the JSON string representation of the object
print(OntologyShaclResult.to_json())

# convert the object into a dict
ontology_shacl_result_dict = ontology_shacl_result_instance.to_dict()
# create an instance of OntologyShaclResult from a dict
ontology_shacl_result_from_dict = OntologyShaclResult.from_dict(ontology_shacl_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


