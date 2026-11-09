# DataSourceUnavailableErrorResponseContent

Returned with HTTP 502 when a backing data source cannot be reached to answer the query; `dataSourceId` identifies the unavailable source.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the error. | 
**data_source_id** | **str** | Identifier of the data source that could not be reached. | [optional] 

## Example

```python
from coa_data_layer_server.models.data_source_unavailable_error_response_content import DataSourceUnavailableErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of DataSourceUnavailableErrorResponseContent from a JSON string
data_source_unavailable_error_response_content_instance = DataSourceUnavailableErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(DataSourceUnavailableErrorResponseContent.to_json())

# convert the object into a dict
data_source_unavailable_error_response_content_dict = data_source_unavailable_error_response_content_instance.to_dict()
# create an instance of DataSourceUnavailableErrorResponseContent from a dict
data_source_unavailable_error_response_content_from_dict = DataSourceUnavailableErrorResponseContent.from_dict(data_source_unavailable_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


