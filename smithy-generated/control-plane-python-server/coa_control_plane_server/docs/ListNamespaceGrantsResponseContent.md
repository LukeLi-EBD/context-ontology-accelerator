# ListNamespaceGrantsResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**grants** | [**List[GrantSummary]**](GrantSummary.md) | The page of namespace grants. | 

## Example

```python
from coa_control_plane_server.models.list_namespace_grants_response_content import ListNamespaceGrantsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListNamespaceGrantsResponseContent from a JSON string
list_namespace_grants_response_content_instance = ListNamespaceGrantsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListNamespaceGrantsResponseContent.to_json())

# convert the object into a dict
list_namespace_grants_response_content_dict = list_namespace_grants_response_content_instance.to_dict()
# create an instance of ListNamespaceGrantsResponseContent from a dict
list_namespace_grants_response_content_from_dict = ListNamespaceGrantsResponseContent.from_dict(list_namespace_grants_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


