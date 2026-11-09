# GetOntologyUploadUrlRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**filename** | **str** | Name of the file to be uploaded. The server sanitizes it and keeps the first 200 characters, so the bound is generous: clients derive the name from the ontology identifier, which may itself be a long IRI. | 
**content_type** | **str** | MIME content type of the file to be uploaded. | [optional] 
**ontology_id** | **str** | Identifier to register the uploaded ontology under. | [optional] 
**title** | **str** | Human-readable display title for the ontology. | [optional] 

## Example

```python
from coa_control_plane_server.models.get_ontology_upload_url_request_content import GetOntologyUploadUrlRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOntologyUploadUrlRequestContent from a JSON string
get_ontology_upload_url_request_content_instance = GetOntologyUploadUrlRequestContent.from_json(json)
# print the JSON string representation of the object
print(GetOntologyUploadUrlRequestContent.to_json())

# convert the object into a dict
get_ontology_upload_url_request_content_dict = get_ontology_upload_url_request_content_instance.to_dict()
# create an instance of GetOntologyUploadUrlRequestContent from a dict
get_ontology_upload_url_request_content_from_dict = GetOntologyUploadUrlRequestContent.from_dict(get_ontology_upload_url_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


