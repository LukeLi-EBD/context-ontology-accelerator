# DownloadOntologyResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**download_url** | **str** | Presigned S3 GET URL for the ontology serialized as Turtle. The ontology is written to the artifacts bucket and served out-of-band rather than inlined, because a large induced ontology (6+ MB) would exceed the API Gateway / Lambda response limit and 502 the call. | 
**expires_in_seconds** | **float** | Seconds until the presigned URL expires. | [optional] 

## Example

```python
from coa_control_plane_server.models.download_ontology_response_content import DownloadOntologyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of DownloadOntologyResponseContent from a JSON string
download_ontology_response_content_instance = DownloadOntologyResponseContent.from_json(json)
# print the JSON string representation of the object
print(DownloadOntologyResponseContent.to_json())

# convert the object into a dict
download_ontology_response_content_dict = download_ontology_response_content_instance.to_dict()
# create an instance of DownloadOntologyResponseContent from a dict
download_ontology_response_content_from_dict = DownloadOntologyResponseContent.from_dict(download_ontology_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


