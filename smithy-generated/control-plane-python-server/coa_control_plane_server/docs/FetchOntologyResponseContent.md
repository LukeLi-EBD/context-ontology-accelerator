# FetchOntologyResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**result** | **object** | Result of the fetch-and-ingest operation. | 

## Example

```python
from coa_control_plane_server.models.fetch_ontology_response_content import FetchOntologyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of FetchOntologyResponseContent from a JSON string
fetch_ontology_response_content_instance = FetchOntologyResponseContent.from_json(json)
# print the JSON string representation of the object
print(FetchOntologyResponseContent.to_json())

# convert the object into a dict
fetch_ontology_response_content_dict = fetch_ontology_response_content_instance.to_dict()
# create an instance of FetchOntologyResponseContent from a dict
fetch_ontology_response_content_from_dict = FetchOntologyResponseContent.from_dict(fetch_ontology_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


