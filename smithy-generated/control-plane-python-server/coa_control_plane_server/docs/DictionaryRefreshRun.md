# DictionaryRefreshRun

Lifecycle of one dictionary introspection pass.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**run_id** | **str** | Server-minted identifier of this introspection pass. | 
**source_id** | **str** | Source whose dictionary was introspected. | 
**status** | **str** | &#x60;running&#x60;, &#x60;succeeded&#x60; or &#x60;failed&#x60;. | 
**idempotency_key** | **str** | Caller-supplied key that makes the refresh replayable. | [optional] 
**requested_by** | **str** | Principal that requested the refresh, when recorded. | [optional] 
**started_at** | **str** | ISO-8601 start time. | [optional] 
**finished_at** | **str** | ISO-8601 finish time; absent while still running. | [optional] 
**processed** | **float** | Column rows read from the source. | [optional] 
**inserted** | **float** | Column rows newly inserted into the snapshot. | [optional] 
**updated** | **float** | Column rows updated in the snapshot. | [optional] 
**unchanged** | **float** | Column rows that were already identical. | [optional] 
**removed** | **float** | Column rows dropped because the source no longer exposes them. | [optional] 
**error** | **str** | Failure message when &#x60;status&#x60; is &#x60;failed&#x60;; absent otherwise. | [optional] 

## Example

```python
from coa_control_plane_server.models.dictionary_refresh_run import DictionaryRefreshRun

# TODO update the JSON string below
json = "{}"
# create an instance of DictionaryRefreshRun from a JSON string
dictionary_refresh_run_instance = DictionaryRefreshRun.from_json(json)
# print the JSON string representation of the object
print(DictionaryRefreshRun.to_json())

# convert the object into a dict
dictionary_refresh_run_dict = dictionary_refresh_run_instance.to_dict()
# create an instance of DictionaryRefreshRun from a dict
dictionary_refresh_run_from_dict = DictionaryRefreshRun.from_dict(dictionary_refresh_run_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


