# ListInducedDatasourcesResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**datasources** | [**List[InducedDatasource]**](InducedDatasource.md) | Data sources that have been successfully inducted. | 

## Example

```python
from coa_control_plane_server.models.list_induced_datasources_response_content import ListInducedDatasourcesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListInducedDatasourcesResponseContent from a JSON string
list_induced_datasources_response_content_instance = ListInducedDatasourcesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListInducedDatasourcesResponseContent.to_json())

# convert the object into a dict
list_induced_datasources_response_content_dict = list_induced_datasources_response_content_instance.to_dict()
# create an instance of ListInducedDatasourcesResponseContent from a dict
list_induced_datasources_response_content_from_dict = ListInducedDatasourcesResponseContent.from_dict(list_induced_datasources_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


