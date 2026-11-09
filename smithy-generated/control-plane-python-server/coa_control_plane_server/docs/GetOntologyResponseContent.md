# GetOntologyResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ontology** | **object** | The requested ontology record. | 

## Example

```python
from coa_control_plane_server.models.get_ontology_response_content import GetOntologyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOntologyResponseContent from a JSON string
get_ontology_response_content_instance = GetOntologyResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetOntologyResponseContent.to_json())

# convert the object into a dict
get_ontology_response_content_dict = get_ontology_response_content_instance.to_dict()
# create an instance of GetOntologyResponseContent from a dict
get_ontology_response_content_from_dict = GetOntologyResponseContent.from_dict(get_ontology_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


