# DictionaryTableSummary

Per-table rollup on the source dictionary page.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**table** | **str** | Table name. | 
**columns** | **float** | Column count in the table. | 
**commented** | **float** | Columns carrying a source comment. | 
**bound** | **float** | Columns bound to an ontology property. | 
**missing_comment** | **float** | Columns with no source comment. | 
**unbound** | **float** | Columns not bound to any ontology property. | 

## Example

```python
from coa_control_plane_server.models.dictionary_table_summary import DictionaryTableSummary

# TODO update the JSON string below
json = "{}"
# create an instance of DictionaryTableSummary from a JSON string
dictionary_table_summary_instance = DictionaryTableSummary.from_json(json)
# print the JSON string representation of the object
print(DictionaryTableSummary.to_json())

# convert the object into a dict
dictionary_table_summary_dict = dictionary_table_summary_instance.to_dict()
# create an instance of DictionaryTableSummary from a dict
dictionary_table_summary_from_dict = DictionaryTableSummary.from_dict(dictionary_table_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


