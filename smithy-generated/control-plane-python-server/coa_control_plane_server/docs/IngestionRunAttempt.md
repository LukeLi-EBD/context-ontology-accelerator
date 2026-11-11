# IngestionRunAttempt

One invocation of `platform import` (platform.import_run).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**run_id** | **str** | Invocation identifier (platform.import_run.run_id), not the batch id. | 
**status** | [**IngestionAttemptStatus**](IngestionAttemptStatus.md) |  | 
**started_at** | **datetime** | When the invocation opened its ledger row. | 
**finished_at** | **datetime** | When the invocation closed its ledger row; absent while running. | [optional] 
**exit_code** | **float** | Process exit code reported by the CLI. | [optional] 
**error_code** | **str** | Machine-readable failure code when status is FAILED. | [optional] 
**error_message** | **str** | Human-readable failure message when status is FAILED. | [optional] 
**counters** | [**IngestionRunCounters**](IngestionRunCounters.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.ingestion_run_attempt import IngestionRunAttempt

# TODO update the JSON string below
json = "{}"
# create an instance of IngestionRunAttempt from a JSON string
ingestion_run_attempt_instance = IngestionRunAttempt.from_json(json)
# print the JSON string representation of the object
print(IngestionRunAttempt.to_json())

# convert the object into a dict
ingestion_run_attempt_dict = ingestion_run_attempt_instance.to_dict()
# create an instance of IngestionRunAttempt from a dict
ingestion_run_attempt_from_dict = IngestionRunAttempt.from_dict(ingestion_run_attempt_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


