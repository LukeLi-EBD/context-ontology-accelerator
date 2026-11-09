# ListSourceTablesResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**items** | [**List[TableSummary]**](TableSummary.md) | Page of table summaries. | 
**skipped_assets** | **float** | Number of assets skipped due to retrieval or parsing failures. Present only when one or more assets could not be loaded, indicating a degraded (partial) response. | [optional] 

## Example

```python
from coa_control_plane_server.models.list_source_tables_response_content import ListSourceTablesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListSourceTablesResponseContent from a JSON string
list_source_tables_response_content_instance = ListSourceTablesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListSourceTablesResponseContent.to_json())

# convert the object into a dict
list_source_tables_response_content_dict = list_source_tables_response_content_instance.to_dict()
# create an instance of ListSourceTablesResponseContent from a dict
list_source_tables_response_content_from_dict = ListSourceTablesResponseContent.from_dict(list_source_tables_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


