# ConflictErrorResponseContent

Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the conflict. | 

## Example

```python
from coa_control_plane_server.models.conflict_error_response_content import ConflictErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ConflictErrorResponseContent from a JSON string
conflict_error_response_content_instance = ConflictErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(ConflictErrorResponseContent.to_json())

# convert the object into a dict
conflict_error_response_content_dict = conflict_error_response_content_instance.to_dict()
# create an instance of ConflictErrorResponseContent from a dict
conflict_error_response_content_from_dict = ConflictErrorResponseContent.from_dict(conflict_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


