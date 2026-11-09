# EmbeddingRecord

One stored embedding, vector included.  Member names mirror the engine's snake_case JSON through `@jsonName`; the camelCase names here are the contract's own spelling.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Row identity. Empty for k-NN hits, which carry no stable external id. | 
**ontology_id** | **str** | Ontology (or A-Box/namespace) the vector belongs to. | 
**entity_uri** | **str** | URI of the embedded entity. | 
**entity_type** | **str** | Entity type the row was written for. | 
**embedding_type** | **str** | Kind of vector in this row. | 
**model_id** | **str** | Model that produced the vector. | 
**dimensions** | **float** | Vector length. | 
**text** | **str** | Source text, when the row was written from text (chunk rows carry it). | [optional] 
**created_at** | **str** | Row creation timestamp (RFC 3339); empty for k-NN hits. | [optional] 
**metadata** | **object** | Provenance metadata, e.g. chunk/document ids for chunk vectors. | [optional] 
**vector** | **List[float]** | The raw vector. | 

## Example

```python
from coa_control_plane_server.models.embedding_record import EmbeddingRecord

# TODO update the JSON string below
json = "{}"
# create an instance of EmbeddingRecord from a JSON string
embedding_record_instance = EmbeddingRecord.from_json(json)
# print the JSON string representation of the object
print(EmbeddingRecord.to_json())

# convert the object into a dict
embedding_record_dict = embedding_record_instance.to_dict()
# create an instance of EmbeddingRecord from a dict
embedding_record_from_dict = EmbeddingRecord.from_dict(embedding_record_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


