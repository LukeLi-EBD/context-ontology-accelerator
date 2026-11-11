# IngestionFailure

One failed item surfaced in the inline failure feed.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**run_id** | **str** | Batch the failed item belongs to. | 
**rel_path** | **str** | Item path relative to the batch root. | 
**attempts** | **float** | Number of processing attempts so far. | 
**code** | **str** | Machine-readable failure code, when the importer recorded one. | [optional] 
**message** | **str** | Human-readable failure message, when the importer recorded one. | [optional] 
**updated_at** | **datetime** | When the item last changed. | 

## Example

```python
from coa_control_plane_server.models.ingestion_failure import IngestionFailure

# TODO update the JSON string below
json = "{}"
# create an instance of IngestionFailure from a JSON string
ingestion_failure_instance = IngestionFailure.from_json(json)
# print the JSON string representation of the object
print(IngestionFailure.to_json())

# convert the object into a dict
ingestion_failure_dict = ingestion_failure_instance.to_dict()
# create an instance of IngestionFailure from a dict
ingestion_failure_from_dict = IngestionFailure.from_dict(ingestion_failure_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


