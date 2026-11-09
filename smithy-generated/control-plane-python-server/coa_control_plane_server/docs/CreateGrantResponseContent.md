# CreateGrantResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**grant** | [**GrantSummary**](GrantSummary.md) |  | 

## Example

```python
from coa_control_plane_server.models.create_grant_response_content import CreateGrantResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of CreateGrantResponseContent from a JSON string
create_grant_response_content_instance = CreateGrantResponseContent.from_json(json)
# print the JSON string representation of the object
print(CreateGrantResponseContent.to_json())

# convert the object into a dict
create_grant_response_content_dict = create_grant_response_content_instance.to_dict()
# create an instance of CreateGrantResponseContent from a dict
create_grant_response_content_from_dict = CreateGrantResponseContent.from_dict(create_grant_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


