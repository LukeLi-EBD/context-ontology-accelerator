# GetOntologyUploadUrlResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**upload_url** | **str** | Presigned S3 URL to PUT the file to. | 
**s3_key** | **str** | S3 object key where the file will be stored. | 
**ontology_id** | **str** | Identifier assigned to the ontology. | 

## Example

```python
from coa_control_plane_server.models.get_ontology_upload_url_response_content import GetOntologyUploadUrlResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOntologyUploadUrlResponseContent from a JSON string
get_ontology_upload_url_response_content_instance = GetOntologyUploadUrlResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetOntologyUploadUrlResponseContent.to_json())

# convert the object into a dict
get_ontology_upload_url_response_content_dict = get_ontology_upload_url_response_content_instance.to_dict()
# create an instance of GetOntologyUploadUrlResponseContent from a dict
get_ontology_upload_url_response_content_from_dict = GetOntologyUploadUrlResponseContent.from_dict(get_ontology_upload_url_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


