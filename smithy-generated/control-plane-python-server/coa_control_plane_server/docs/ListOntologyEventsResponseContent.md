# ListOntologyEventsResponseContent

Audit page for one ontology.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[OntologyEvent]**](OntologyEvent.md) | Events, newest first. | 
**count** | **float** | Number of events returned. | 
**categories** | **Dict[str, float]** | Counts per audit category. | [optional] 
**filter** | [**OntologyEventFilter**](OntologyEventFilter.md) |  | [optional] 
**current** | [**OntologyPointer**](OntologyPointer.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.list_ontology_events_response_content import ListOntologyEventsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListOntologyEventsResponseContent from a JSON string
list_ontology_events_response_content_instance = ListOntologyEventsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListOntologyEventsResponseContent.to_json())

# convert the object into a dict
list_ontology_events_response_content_dict = list_ontology_events_response_content_instance.to_dict()
# create an instance of ListOntologyEventsResponseContent from a dict
list_ontology_events_response_content_from_dict = ListOntologyEventsResponseContent.from_dict(list_ontology_events_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


