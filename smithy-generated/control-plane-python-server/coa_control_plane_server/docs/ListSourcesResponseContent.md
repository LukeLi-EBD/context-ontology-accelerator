# ListSourcesResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**items** | [**List[SourceSummary]**](SourceSummary.md) | Page of source summaries. | 

## Example

```python
from coa_control_plane_server.models.list_sources_response_content import ListSourcesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListSourcesResponseContent from a JSON string
list_sources_response_content_instance = ListSourcesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListSourcesResponseContent.to_json())

# convert the object into a dict
list_sources_response_content_dict = list_sources_response_content_instance.to_dict()
# create an instance of ListSourcesResponseContent from a dict
list_sources_response_content_from_dict = ListSourcesResponseContent.from_dict(list_sources_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


