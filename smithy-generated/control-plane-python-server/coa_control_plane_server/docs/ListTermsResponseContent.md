# ListTermsResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**namespace_id** | **str** | UUID v4 identifier. | 
**graph** | **str** | IRI of the graph the entries were read from; absent when the namespace has no lexicon graph. | [optional] 
**counts** | [**TermCounts**](TermCounts.md) |  | 
**entries** | [**List[TermEntry]**](TermEntry.md) | The alias rows for this page. | 
**total** | **float** | Number of entries after filtering. | 
**offset** | **float** | Number of rows skipped. | 
**limit** | **float** | Page size actually applied. | 

## Example

```python
from coa_control_plane_server.models.list_terms_response_content import ListTermsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListTermsResponseContent from a JSON string
list_terms_response_content_instance = ListTermsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListTermsResponseContent.to_json())

# convert the object into a dict
list_terms_response_content_dict = list_terms_response_content_instance.to_dict()
# create an instance of ListTermsResponseContent from a dict
list_terms_response_content_from_dict = ListTermsResponseContent.from_dict(list_terms_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


