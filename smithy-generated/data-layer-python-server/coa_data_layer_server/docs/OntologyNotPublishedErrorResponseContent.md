# OntologyNotPublishedErrorResponseContent

Returned with HTTP 409 when the namespace has no published ontology, so the query cannot be resolved against a schema yet.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** | Human-readable description of the error. | 
**namespace_id** | **str** | Identifier of the namespace whose ontology is not published. | [optional] 

## Example

```python
from coa_data_layer_server.models.ontology_not_published_error_response_content import OntologyNotPublishedErrorResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyNotPublishedErrorResponseContent from a JSON string
ontology_not_published_error_response_content_instance = OntologyNotPublishedErrorResponseContent.from_json(json)
# print the JSON string representation of the object
print(OntologyNotPublishedErrorResponseContent.to_json())

# convert the object into a dict
ontology_not_published_error_response_content_dict = ontology_not_published_error_response_content_instance.to_dict()
# create an instance of OntologyNotPublishedErrorResponseContent from a dict
ontology_not_published_error_response_content_from_dict = OntologyNotPublishedErrorResponseContent.from_dict(ontology_not_published_error_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


