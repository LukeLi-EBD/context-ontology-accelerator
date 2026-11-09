# LoadFoundationalOntologyRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**client_token** | **str** | Optional idempotency token. A retry with the same token within 24 hours returns the original job handle instead of starting a second load; reusing the token for a different key is rejected with a 409. | [optional] 

## Example

```python
from coa_control_plane_server.models.load_foundational_ontology_request_content import LoadFoundationalOntologyRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of LoadFoundationalOntologyRequestContent from a JSON string
load_foundational_ontology_request_content_instance = LoadFoundationalOntologyRequestContent.from_json(json)
# print the JSON string representation of the object
print(LoadFoundationalOntologyRequestContent.to_json())

# convert the object into a dict
load_foundational_ontology_request_content_dict = load_foundational_ontology_request_content_instance.to_dict()
# create an instance of LoadFoundationalOntologyRequestContent from a dict
load_foundational_ontology_request_content_from_dict = LoadFoundationalOntologyRequestContent.from_dict(load_foundational_ontology_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


