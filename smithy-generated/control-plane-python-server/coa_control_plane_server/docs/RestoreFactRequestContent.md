# RestoreFactRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**actor** | **str** | Identity recorded on the restore event; defaults to &#x60;api&#x60;. | [optional] 
**reason** | **str** | Why the row is restored. | [optional] 

## Example

```python
from coa_control_plane_server.models.restore_fact_request_content import RestoreFactRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RestoreFactRequestContent from a JSON string
restore_fact_request_content_instance = RestoreFactRequestContent.from_json(json)
# print the JSON string representation of the object
print(RestoreFactRequestContent.to_json())

# convert the object into a dict
restore_fact_request_content_dict = restore_fact_request_content_instance.to_dict()
# create an instance of RestoreFactRequestContent from a dict
restore_fact_request_content_from_dict = RestoreFactRequestContent.from_dict(restore_fact_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


