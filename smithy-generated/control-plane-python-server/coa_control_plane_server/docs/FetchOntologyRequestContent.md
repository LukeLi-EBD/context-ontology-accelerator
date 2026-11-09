# FetchOntologyRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_url** | **str** | Source URL to fetch the ontology from. HTTPS only. | [optional] 

## Example

```python
from coa_control_plane_server.models.fetch_ontology_request_content import FetchOntologyRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of FetchOntologyRequestContent from a JSON string
fetch_ontology_request_content_instance = FetchOntologyRequestContent.from_json(json)
# print the JSON string representation of the object
print(FetchOntologyRequestContent.to_json())

# convert the object into a dict
fetch_ontology_request_content_dict = fetch_ontology_request_content_instance.to_dict()
# create an instance of FetchOntologyRequestContent from a dict
fetch_ontology_request_content_from_dict = FetchOntologyRequestContent.from_dict(fetch_ontology_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


