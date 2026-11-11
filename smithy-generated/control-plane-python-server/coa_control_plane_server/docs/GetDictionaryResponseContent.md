# GetDictionaryResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Source the dictionary belongs to. | 
**source_kind** | **str** | Source engine kind, e.g. &#x60;postgresql&#x60; or &#x60;snowflake&#x60;. | [optional] 
**catalog** | **str** | Catalog the source exposes tables under. | [optional] 
**var_schema** | **str** | Schema the source exposes tables under. | [optional] 
**tables** | [**List[DictionaryTableSummary]**](DictionaryTableSummary.md) | Per-table rollups. | 
**totals** | [**CommentCoverage**](CommentCoverage.md) |  | 
**bound_columns** | **float** | Bindings already resolved (&#x60;binding_method&#x60; !&#x3D; &#x60;none&#x60;). | 
**latest_run** | [**DictionaryRefreshRun**](DictionaryRefreshRun.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.get_dictionary_response_content import GetDictionaryResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetDictionaryResponseContent from a JSON string
get_dictionary_response_content_instance = GetDictionaryResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetDictionaryResponseContent.to_json())

# convert the object into a dict
get_dictionary_response_content_dict = get_dictionary_response_content_instance.to_dict()
# create an instance of GetDictionaryResponseContent from a dict
get_dictionary_response_content_from_dict = GetDictionaryResponseContent.from_dict(get_dictionary_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


