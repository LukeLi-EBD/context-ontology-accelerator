# GetDictionaryViewResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[DictionaryColumn]**](DictionaryColumn.md) | Column rows for this page. | 
**total** | **float** | Number of rows after filtering. | 
**offset** | **float** | Number of rows skipped. | 
**limit** | **float** | Page size actually applied. | 
**view** | **str** | The filter view that was applied. | 
**coverage** | [**CommentCoverage**](CommentCoverage.md) |  | 
**warnings** | **List[str]** | Non-fatal notes, e.g. an empty mappable set. Never silent. | [optional] 

## Example

```python
from coa_control_plane_server.models.get_dictionary_view_response_content import GetDictionaryViewResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetDictionaryViewResponseContent from a JSON string
get_dictionary_view_response_content_instance = GetDictionaryViewResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetDictionaryViewResponseContent.to_json())

# convert the object into a dict
get_dictionary_view_response_content_dict = get_dictionary_view_response_content_instance.to_dict()
# create an instance of GetDictionaryViewResponseContent from a dict
get_dictionary_view_response_content_from_dict = GetDictionaryViewResponseContent.from_dict(get_dictionary_view_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


