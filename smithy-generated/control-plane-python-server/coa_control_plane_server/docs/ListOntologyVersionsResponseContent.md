# ListOntologyVersionsResponseContent

Page of versions for one ontology.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[OntologyVersion]**](OntologyVersion.md) | Versions in creation order. | 
**count** | **float** | Number of versions returned. | 
**total** | **float** | Number of versions before the deprecated filter. | 
**deprecated** | **float** | Deprecated versions filtered out of &#x60;items&#x60;. | 
**pointer** | [**OntologyPointer**](OntologyPointer.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.list_ontology_versions_response_content import ListOntologyVersionsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListOntologyVersionsResponseContent from a JSON string
list_ontology_versions_response_content_instance = ListOntologyVersionsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListOntologyVersionsResponseContent.to_json())

# convert the object into a dict
list_ontology_versions_response_content_dict = list_ontology_versions_response_content_instance.to_dict()
# create an instance of ListOntologyVersionsResponseContent from a dict
list_ontology_versions_response_content_from_dict = ListOntologyVersionsResponseContent.from_dict(list_ontology_versions_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


