# DictionarySummary

Per-source rollup shown in the source list.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Source the snapshot belongs to. | 
**source_kind** | **str** | Source engine kind, e.g. &#x60;postgresql&#x60; or &#x60;snowflake&#x60;. | 
**tables** | **float** | Distinct tables in the snapshot. | 
**columns** | **float** | Column count in the snapshot. | 
**commented** | **float** | Columns carrying a source comment. | 
**bound** | **float** | Columns bound to an ontology property. | 
**observed_at** | **str** | ISO-8601 time the snapshot was last observed. | [optional] 
**last_run** | [**DictionaryRefreshRun**](DictionaryRefreshRun.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.dictionary_summary import DictionarySummary

# TODO update the JSON string below
json = "{}"
# create an instance of DictionarySummary from a JSON string
dictionary_summary_instance = DictionarySummary.from_json(json)
# print the JSON string representation of the object
print(DictionarySummary.to_json())

# convert the object into a dict
dictionary_summary_dict = dictionary_summary_instance.to_dict()
# create an instance of DictionarySummary from a dict
dictionary_summary_from_dict = DictionarySummary.from_dict(dictionary_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


