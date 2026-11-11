# ListDictionariesResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[DictionarySummary]**](DictionarySummary.md) | Per-source dictionary rollups for this page. | 
**total** | **float** | Number of sources that have a snapshot. | 
**offset** | **float** | Number of rows skipped. | 
**limit** | **float** | Page size actually applied. | 

## Example

```python
from coa_control_plane_server.models.list_dictionaries_response_content import ListDictionariesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListDictionariesResponseContent from a JSON string
list_dictionaries_response_content_instance = ListDictionariesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListDictionariesResponseContent.to_json())

# convert the object into a dict
list_dictionaries_response_content_dict = list_dictionaries_response_content_instance.to_dict()
# create an instance of ListDictionariesResponseContent from a dict
list_dictionaries_response_content_from_dict = ListDictionariesResponseContent.from_dict(list_dictionaries_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


