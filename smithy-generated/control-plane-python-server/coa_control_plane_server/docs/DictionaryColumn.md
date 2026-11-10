# DictionaryColumn

One column row in the dictionary (ten-column view, F63).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Source this column snapshot belongs to. | 
**catalog** | **str** | Catalog the source exposes the table under. | 
**var_schema** | **str** | Schema the source exposes the table under. | 
**table** | **str** | Table name. | 
**column** | **str** | Column name. | 
**data_type** | **str** | Column data type as reported by the source. | 
**is_nullable** | **bool** | Whether the column admits NULL. | 
**source_kind** | **str** | Source engine kind, e.g. &#x60;postgresql&#x60; or &#x60;snowflake&#x60;. | 
**binding_method** | **str** | How the binding was resolved: &#x60;explicit&#x60;, &#x60;name_match&#x60;, &#x60;manual&#x60; or &#x60;none&#x60;. | 
**comment** | **str** | Column comment captured from the source, when present. | [optional] 
**property_iri** | **str** | Ontology property this column is bound to, when bound. | [optional] 
**confidence** | **float** | Confidence of a &#x60;name_match&#x60; binding, 0..1. | [optional] 
**binding_note** | **str** | Human note attached to a &#x60;manual&#x60; binding. | [optional] 
**observed_at** | **str** | ISO-8601 time the snapshot observed this column. | [optional] 
**last_refresh_run_id** | **str** | Refresh run that last wrote this row. | [optional] 

## Example

```python
from coa_control_plane_server.models.dictionary_column import DictionaryColumn

# TODO update the JSON string below
json = "{}"
# create an instance of DictionaryColumn from a JSON string
dictionary_column_instance = DictionaryColumn.from_json(json)
# print the JSON string representation of the object
print(DictionaryColumn.to_json())

# convert the object into a dict
dictionary_column_dict = dictionary_column_instance.to_dict()
# create an instance of DictionaryColumn from a dict
dictionary_column_from_dict = DictionaryColumn.from_dict(dictionary_column_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


