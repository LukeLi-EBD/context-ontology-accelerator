# ListPrincipalGrantsResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**grants** | [**List[GrantSummary]**](GrantSummary.md) | The page of namespace grants held by the principal. | 

## Example

```python
from coa_control_plane_server.models.list_principal_grants_response_content import ListPrincipalGrantsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListPrincipalGrantsResponseContent from a JSON string
list_principal_grants_response_content_instance = ListPrincipalGrantsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListPrincipalGrantsResponseContent.to_json())

# convert the object into a dict
list_principal_grants_response_content_dict = list_principal_grants_response_content_instance.to_dict()
# create an instance of ListPrincipalGrantsResponseContent from a dict
list_principal_grants_response_content_from_dict = ListPrincipalGrantsResponseContent.from_dict(list_principal_grants_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


