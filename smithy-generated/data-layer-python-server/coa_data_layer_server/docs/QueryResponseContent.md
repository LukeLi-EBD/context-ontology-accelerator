# QueryResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**result** | [**QueryResult**](QueryResult.md) |  | 
**request_id** | **str** | Identifier of the request, for tracing and support. | [optional] 
**session_id** | **str** | Identifier of the session the request belongs to. | [optional] 

## Example

```python
from coa_data_layer_server.models.query_response_content import QueryResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of QueryResponseContent from a JSON string
query_response_content_instance = QueryResponseContent.from_json(json)
# print the JSON string representation of the object
print(QueryResponseContent.to_json())

# convert the object into a dict
query_response_content_dict = query_response_content_instance.to_dict()
# create an instance of QueryResponseContent from a dict
query_response_content_from_dict = QueryResponseContent.from_dict(query_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


