# RefreshDictionariesRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**idempotency_key** | **str** | Caller-supplied key; generated per request when absent. | [optional] 
**requested_by** | **str** | Principal requesting the refresh, when the caller supplies one. | [optional] 

## Example

```python
from coa_control_plane_server.models.refresh_dictionaries_request_content import RefreshDictionariesRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RefreshDictionariesRequestContent from a JSON string
refresh_dictionaries_request_content_instance = RefreshDictionariesRequestContent.from_json(json)
# print the JSON string representation of the object
print(RefreshDictionariesRequestContent.to_json())

# convert the object into a dict
refresh_dictionaries_request_content_dict = refresh_dictionaries_request_content_instance.to_dict()
# create an instance of RefreshDictionariesRequestContent from a dict
refresh_dictionaries_request_content_from_dict = RefreshDictionariesRequestContent.from_dict(refresh_dictionaries_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


