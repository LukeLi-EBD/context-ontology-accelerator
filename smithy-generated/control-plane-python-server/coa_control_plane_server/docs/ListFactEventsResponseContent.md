# ListFactEventsResponseContent

One page of a fact's event chain.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fact_id** | **str** | Fact the page belongs to. | 
**count** | **float** | Number of events in this page. | 
**total** | **float** | Total number of events on the chain. | 
**items** | [**List[FactEvent]**](FactEvent.md) | Events, newest first. | 
**next_before** | **float** | Pass back as &#x60;before&#x60; to page further back; absent at the start. | [optional] 

## Example

```python
from coa_control_plane_server.models.list_fact_events_response_content import ListFactEventsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListFactEventsResponseContent from a JSON string
list_fact_events_response_content_instance = ListFactEventsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListFactEventsResponseContent.to_json())

# convert the object into a dict
list_fact_events_response_content_dict = list_fact_events_response_content_instance.to_dict()
# create an instance of ListFactEventsResponseContent from a dict
list_fact_events_response_content_from_dict = ListFactEventsResponseContent.from_dict(list_fact_events_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


