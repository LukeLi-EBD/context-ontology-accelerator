# ListNamespacesResponseContent

Output of ListNamespaces: a page of namespace summaries plus an optional pagination token.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**namespaces** | [**List[NamespaceSummary]**](NamespaceSummary.md) | The page of namespace summaries. | 

## Example

```python
from coa_control_plane_server.models.list_namespaces_response_content import ListNamespacesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListNamespacesResponseContent from a JSON string
list_namespaces_response_content_instance = ListNamespacesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListNamespacesResponseContent.to_json())

# convert the object into a dict
list_namespaces_response_content_dict = list_namespaces_response_content_instance.to_dict()
# create an instance of ListNamespacesResponseContent from a dict
list_namespaces_response_content_from_dict = ListNamespacesResponseContent.from_dict(list_namespaces_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


