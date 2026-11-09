# ListFoundationalOntologiesResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[FoundationalOntologySummary]**](FoundationalOntologySummary.md) | Catalog of foundational ontologies available for grounding. | 

## Example

```python
from coa_control_plane_server.models.list_foundational_ontologies_response_content import ListFoundationalOntologiesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListFoundationalOntologiesResponseContent from a JSON string
list_foundational_ontologies_response_content_instance = ListFoundationalOntologiesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListFoundationalOntologiesResponseContent.to_json())

# convert the object into a dict
list_foundational_ontologies_response_content_dict = list_foundational_ontologies_response_content_instance.to_dict()
# create an instance of ListFoundationalOntologiesResponseContent from a dict
list_foundational_ontologies_response_content_from_dict = ListFoundationalOntologiesResponseContent.from_dict(list_foundational_ontologies_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


