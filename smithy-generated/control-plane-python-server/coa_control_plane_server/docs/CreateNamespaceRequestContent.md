# CreateNamespaceRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Namespace name: 3-64 lowercase alphanumeric or hyphens, must start/end with alphanumeric. | 
**display_name** | **str** | Display name for a namespace. Angle brackets and control characters are rejected. | [optional] 
**description** | **str** | Namespace description. Angle brackets and control characters other than tab and newline are rejected. | [optional] 
**owner** | **str** | Owner email address. The local part allows the RFC 5322 atext characters except # | and backtick (the owner also becomes a grant principalId). Personal information, so marked sensitive to keep it out of generated-client logs. | 
**language** | **str** | Language of the sources, ontology and knowledge graph this namespace will hold. Defaults to &#x60;en&#x60; when omitted. Cannot be changed after creation. | [optional] 
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original result instead of creating a duplicate; reusing the token with different parameters is rejected with ConflictError (409). | [optional] 

## Example

```python
from coa_control_plane_server.models.create_namespace_request_content import CreateNamespaceRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of CreateNamespaceRequestContent from a JSON string
create_namespace_request_content_instance = CreateNamespaceRequestContent.from_json(json)
# print the JSON string representation of the object
print(CreateNamespaceRequestContent.to_json())

# convert the object into a dict
create_namespace_request_content_dict = create_namespace_request_content_instance.to_dict()
# create an instance of CreateNamespaceRequestContent from a dict
create_namespace_request_content_from_dict = CreateNamespaceRequestContent.from_dict(create_namespace_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


