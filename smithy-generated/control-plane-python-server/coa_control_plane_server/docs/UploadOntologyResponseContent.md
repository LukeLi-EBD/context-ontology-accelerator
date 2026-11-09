# UploadOntologyResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**result** | **object** | Result of the upload operation. | 

## Example

```python
from coa_control_plane_server.models.upload_ontology_response_content import UploadOntologyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of UploadOntologyResponseContent from a JSON string
upload_ontology_response_content_instance = UploadOntologyResponseContent.from_json(json)
# print the JSON string representation of the object
print(UploadOntologyResponseContent.to_json())

# convert the object into a dict
upload_ontology_response_content_dict = upload_ontology_response_content_instance.to_dict()
# create an instance of UploadOntologyResponseContent from a dict
upload_ontology_response_content_from_dict = UploadOntologyResponseContent.from_dict(upload_ontology_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


