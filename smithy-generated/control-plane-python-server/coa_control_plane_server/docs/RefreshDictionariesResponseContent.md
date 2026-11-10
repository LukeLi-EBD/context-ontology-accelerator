# RefreshDictionariesResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**run** | [**DictionaryRefreshRun**](DictionaryRefreshRun.md) |  | 
**binding_basis** | **str** | How bindings were resolved: &#x60;published-ontology&#x60;, &#x60;published-ontology-empty&#x60;, or &#x60;replay&#x60; when an already-succeeded idempotency key returned its prior run. | 
**warnings** | **List[str]** | Non-fatal notes (e.g. a source with zero columns). Never silent. | [optional] 

## Example

```python
from coa_control_plane_server.models.refresh_dictionaries_response_content import RefreshDictionariesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RefreshDictionariesResponseContent from a JSON string
refresh_dictionaries_response_content_instance = RefreshDictionariesResponseContent.from_json(json)
# print the JSON string representation of the object
print(RefreshDictionariesResponseContent.to_json())

# convert the object into a dict
refresh_dictionaries_response_content_dict = refresh_dictionaries_response_content_instance.to_dict()
# create an instance of RefreshDictionariesResponseContent from a dict
refresh_dictionaries_response_content_from_dict = RefreshDictionariesResponseContent.from_dict(refresh_dictionaries_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


