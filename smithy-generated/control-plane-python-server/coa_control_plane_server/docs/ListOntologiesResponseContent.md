# ListOntologiesResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**ontologies** | [**List[OntologyRecord]**](OntologyRecord.md) | The ontologies registered in the namespace. | 

## Example

```python
from coa_control_plane_server.models.list_ontologies_response_content import ListOntologiesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListOntologiesResponseContent from a JSON string
list_ontologies_response_content_instance = ListOntologiesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListOntologiesResponseContent.to_json())

# convert the object into a dict
list_ontologies_response_content_dict = list_ontologies_response_content_instance.to_dict()
# create an instance of ListOntologiesResponseContent from a dict
list_ontologies_response_content_from_dict = ListOntologiesResponseContent.from_dict(list_ontologies_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


