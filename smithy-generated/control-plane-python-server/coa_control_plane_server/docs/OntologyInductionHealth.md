# OntologyInductionHealth

Health of the ontology-induction subsystem's dependencies: the graph store (Neptune Analytics), vector store (OpenSearch), Bedrock embeddings backend, and description LLM (Bedrock Converse).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**graph_store** | **str** | Graph store (Neptune Analytics) status | [optional] 
**vector_store** | **str** | Vector store (OpenSearch) status | [optional] 
**bedrock_embeddings** | **str** | Bedrock embeddings backend status | [optional] 
**description_llm** | **str** | Description LLM (Bedrock Converse) status | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_induction_health import OntologyInductionHealth

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyInductionHealth from a JSON string
ontology_induction_health_instance = OntologyInductionHealth.from_json(json)
# print the JSON string representation of the object
print(OntologyInductionHealth.to_json())

# convert the object into a dict
ontology_induction_health_dict = ontology_induction_health_instance.to_dict()
# create an instance of OntologyInductionHealth from a dict
ontology_induction_health_from_dict = OntologyInductionHealth.from_dict(ontology_induction_health_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


