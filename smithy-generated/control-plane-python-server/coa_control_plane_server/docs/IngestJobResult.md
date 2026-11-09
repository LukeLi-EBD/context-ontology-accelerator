# IngestJobResult

Counts produced once an ingest job completes.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ontology_id** | **str** | Identifier of the ingested ontology. | [optional] 
**class_count** | **float** | Number of classes ingested. | [optional] 
**embedding_count** | **float** | Number of embeddings generated. | [optional] 

## Example

```python
from coa_control_plane_server.models.ingest_job_result import IngestJobResult

# TODO update the JSON string below
json = "{}"
# create an instance of IngestJobResult from a JSON string
ingest_job_result_instance = IngestJobResult.from_json(json)
# print the JSON string representation of the object
print(IngestJobResult.to_json())

# convert the object into a dict
ingest_job_result_dict = ingest_job_result_instance.to_dict()
# create an instance of IngestJobResult from a dict
ingest_job_result_from_dict = IngestJobResult.from_dict(ingest_job_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


