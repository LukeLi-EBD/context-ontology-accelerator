# IngestJob

Async ingest job handle / status — returned by ingest-from-s3 (202) and the ingest-status poll. Typed so FE/BE share one contract.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | Identifier of the async ingest job. | 
**ontology_id** | **str** | Identifier of the ontology being ingested. | 
**status** | [**IngestJobState**](IngestJobState.md) |  | 
**error** | **str** | Error message when the job failed; absent otherwise. | [optional] 
**result** | [**IngestJobResult**](IngestJobResult.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.ingest_job import IngestJob

# TODO update the JSON string below
json = "{}"
# create an instance of IngestJob from a JSON string
ingest_job_instance = IngestJob.from_json(json)
# print the JSON string representation of the object
print(IngestJob.to_json())

# convert the object into a dict
ingest_job_dict = ingest_job_instance.to_dict()
# create an instance of IngestJob from a dict
ingest_job_from_dict = IngestJob.from_dict(ingest_job_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


