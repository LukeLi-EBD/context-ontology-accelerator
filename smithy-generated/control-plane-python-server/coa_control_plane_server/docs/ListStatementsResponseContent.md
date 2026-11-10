# ListStatementsResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**statements** | [**List[GraphStatement]**](GraphStatement.md) | The page of matching statements, in the backend&#39;s named-graph index order (stable for a static graph, not a sorted order). | 
**truncated** | **bool** | True when the page was capped at &#x60;&#x60;limit&#x60;&#x60; and more statements exist beyond this window. | [optional] 

## Example

```python
from coa_control_plane_server.models.list_statements_response_content import ListStatementsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListStatementsResponseContent from a JSON string
list_statements_response_content_instance = ListStatementsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListStatementsResponseContent.to_json())

# convert the object into a dict
list_statements_response_content_dict = list_statements_response_content_instance.to_dict()
# create an instance of ListStatementsResponseContent from a dict
list_statements_response_content_from_dict = ListStatementsResponseContent.from_dict(list_statements_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


