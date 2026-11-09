# ListDocumentsResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**items** | [**List[DocumentSummary]**](DocumentSummary.md) | Page of document summaries. | 

## Example

```python
from coa_control_plane_server.models.list_documents_response_content import ListDocumentsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListDocumentsResponseContent from a JSON string
list_documents_response_content_instance = ListDocumentsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListDocumentsResponseContent.to_json())

# convert the object into a dict
list_documents_response_content_dict = list_documents_response_content_instance.to_dict()
# create an instance of ListDocumentsResponseContent from a dict
list_documents_response_content_from_dict = ListDocumentsResponseContent.from_dict(list_documents_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


