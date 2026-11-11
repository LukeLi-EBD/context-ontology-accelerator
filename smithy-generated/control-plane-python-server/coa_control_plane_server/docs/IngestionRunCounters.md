# IngestionRunCounters

Counters exactly as reported by one invocation.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | **float** | Items discovered by this scan. | 
**already_done** | **float** | Items that were already embedded before this invocation. | 
**processed** | **float** | Items this invocation reached a terminal state for. | 
**parsed** | **float** | Items successfully parsed. | 
**resumed_chunked** | **float** | Items that resumed from a previous chunking step. | 
**indexed** | **float** | Items indexed with vectors in the active model partition. | 
**documents_added** | **float** | Document rows created by this invocation. | 
**failed_this_run** | **float** | Items that failed during this invocation. | 
**failed_total** | **float** | Items still marked failed at the end of this invocation. | 
**remaining_files** | **float** | Items left pending, parsing or chunked when the invocation stopped. | 
**interrupted** | **bool** | True when the invocation stopped at a segment boundary and can resume. | 
**skipped** | [**IngestionRunSkipped**](IngestionRunSkipped.md) |  | 
**elapsed_seconds** | **float** | Wall-clock duration of the invocation. | 

## Example

```python
from coa_control_plane_server.models.ingestion_run_counters import IngestionRunCounters

# TODO update the JSON string below
json = "{}"
# create an instance of IngestionRunCounters from a JSON string
ingestion_run_counters_instance = IngestionRunCounters.from_json(json)
# print the JSON string representation of the object
print(IngestionRunCounters.to_json())

# convert the object into a dict
ingestion_run_counters_dict = ingestion_run_counters_instance.to_dict()
# create an instance of IngestionRunCounters from a dict
ingestion_run_counters_from_dict = IngestionRunCounters.from_dict(ingestion_run_counters_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


