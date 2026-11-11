# IngestionRun

One import batch and its per-item counters.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**run_id** | **str** | Stable batch identifier (platform.import_batch.batch_id). | 
**root** | **str** | Filesystem root that was imported. | 
**status** | [**IngestionRunStatus**](IngestionRunStatus.md) |  | 
**stale** | **bool** | True when status is STALE. | 
**stale_reason** | **str** | Machine-readable stale reason; present only when stale is true. | [optional] 
**total** | **float** | Discovered items in this batch. | 
**completed** | **float** | Items that reached a terminal state (indexed or failed). | 
**indexed** | **float** | Items indexed successfully. | 
**failed** | **float** | Items that ended in failure. | 
**degraded** | **float** | Items indexed with degraded quality (for example missing embeddings). | 
**created_at** | **datetime** | When the batch row was created. | 
**updated_at** | **datetime** | When the batch row last changed. | 
**finished_at** | **datetime** | When the batch finished; absent while running. | [optional] 
**last_run** | [**IngestionRunAttempt**](IngestionRunAttempt.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.ingestion_run import IngestionRun

# TODO update the JSON string below
json = "{}"
# create an instance of IngestionRun from a JSON string
ingestion_run_instance = IngestionRun.from_json(json)
# print the JSON string representation of the object
print(IngestionRun.to_json())

# convert the object into a dict
ingestion_run_dict = ingestion_run_instance.to_dict()
# create an instance of IngestionRun from a dict
ingestion_run_from_dict = IngestionRun.from_dict(ingestion_run_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


