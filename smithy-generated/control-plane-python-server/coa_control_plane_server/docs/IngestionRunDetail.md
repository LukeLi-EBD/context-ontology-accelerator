# IngestionRunDetail

One import batch with its latest invocation and its per-item rows.

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
**items** | [**List[IngestionRunItem]**](IngestionRunItem.md) | Per-file rows of this batch, ordered by relative path (at most 1000). | 

## Example

```python
from coa_control_plane_server.models.ingestion_run_detail import IngestionRunDetail

# TODO update the JSON string below
json = "{}"
# create an instance of IngestionRunDetail from a JSON string
ingestion_run_detail_instance = IngestionRunDetail.from_json(json)
# print the JSON string representation of the object
print(IngestionRunDetail.to_json())

# convert the object into a dict
ingestion_run_detail_dict = ingestion_run_detail_instance.to_dict()
# create an instance of IngestionRunDetail from a dict
ingestion_run_detail_from_dict = IngestionRunDetail.from_dict(ingestion_run_detail_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


