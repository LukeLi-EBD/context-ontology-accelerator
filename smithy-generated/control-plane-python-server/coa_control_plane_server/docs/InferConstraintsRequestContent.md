# InferConstraintsRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original job handle instead of starting a second job; reusing the token with different parameters is rejected with a 409. | [optional] 

## Example

```python
from coa_control_plane_server.models.infer_constraints_request_content import InferConstraintsRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of InferConstraintsRequestContent from a JSON string
infer_constraints_request_content_instance = InferConstraintsRequestContent.from_json(json)
# print the JSON string representation of the object
print(InferConstraintsRequestContent.to_json())

# convert the object into a dict
infer_constraints_request_content_dict = infer_constraints_request_content_instance.to_dict()
# create an instance of InferConstraintsRequestContent from a dict
infer_constraints_request_content_from_dict = InferConstraintsRequestContent.from_dict(infer_constraints_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


