# IngestOntologyFromS3RequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**s3_key** | **str** | S3 object key of the uploaded ontology file, as returned by GetOntologyUploadUrl. | 
**format** | [**OntologyFileFormat**](OntologyFileFormat.md) |  | [optional] 
**title** | **str** | Human-readable display title for the ontology. | [optional] 
**ontology_type** | [**OntologyType**](OntologyType.md) |  | [optional] 
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original result instead of starting a second ingest job; reusing the token with different parameters is rejected with a 409. | [optional] 

## Example

```python
from coa_control_plane_server.models.ingest_ontology_from_s3_request_content import IngestOntologyFromS3RequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of IngestOntologyFromS3RequestContent from a JSON string
ingest_ontology_from_s3_request_content_instance = IngestOntologyFromS3RequestContent.from_json(json)
# print the JSON string representation of the object
print(IngestOntologyFromS3RequestContent.to_json())

# convert the object into a dict
ingest_ontology_from_s3_request_content_dict = ingest_ontology_from_s3_request_content_instance.to_dict()
# create an instance of IngestOntologyFromS3RequestContent from a dict
ingest_ontology_from_s3_request_content_from_dict = IngestOntologyFromS3RequestContent.from_dict(ingest_ontology_from_s3_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


