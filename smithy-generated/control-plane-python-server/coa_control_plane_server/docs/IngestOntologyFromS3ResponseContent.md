# IngestOntologyFromS3ResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**result** | [**IngestJob**](IngestJob.md) |  | 

## Example

```python
from coa_control_plane_server.models.ingest_ontology_from_s3_response_content import IngestOntologyFromS3ResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of IngestOntologyFromS3ResponseContent from a JSON string
ingest_ontology_from_s3_response_content_instance = IngestOntologyFromS3ResponseContent.from_json(json)
# print the JSON string representation of the object
print(IngestOntologyFromS3ResponseContent.to_json())

# convert the object into a dict
ingest_ontology_from_s3_response_content_dict = ingest_ontology_from_s3_response_content_instance.to_dict()
# create an instance of IngestOntologyFromS3ResponseContent from a dict
ingest_ontology_from_s3_response_content_from_dict = IngestOntologyFromS3ResponseContent.from_dict(ingest_ontology_from_s3_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


