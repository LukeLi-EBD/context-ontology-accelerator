# OntologyEvent

One row of the hash-chained lifecycle audit log.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**event_id** | **float** | Monotonic event identifier. | 
**version_id** | **str** | Version the event belongs to. | [optional] 
**proposal_id** | **str** | Proposal the event belongs to. | [optional] 
**action** | **str** | Action recorded, e.g. &#x60;published&#x60;, &#x60;rolled_back&#x60;, &#x60;approved&#x60;. | 
**actor** | **str** | Who performed the action. | 
**reason** | **str** | Optional reason recorded with the action. | [optional] 
**payload** | **object** | Action payload, as the kernel stored it. | [optional] 
**prev_event** | **float** | Previous event identifier in the chain. | [optional] 
**hash** | **str** | Hash of this event. | [optional] 
**created_at** | **str** | Event time (ISO-8601). | 
**type** | **str** | Alias of &#x60;action&#x60;, kept for older callers. | [optional] 
**at** | **str** | Alias of &#x60;createdAt&#x60;, kept for older callers. | [optional] 
**category** | **str** | &#x60;published&#x60;, &#x60;rolled_back&#x60;, &#x60;superseded&#x60;, or &#x60;other&#x60;. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_event import OntologyEvent

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyEvent from a JSON string
ontology_event_instance = OntologyEvent.from_json(json)
# print the JSON string representation of the object
print(OntologyEvent.to_json())

# convert the object into a dict
ontology_event_dict = ontology_event_instance.to_dict()
# create an instance of OntologyEvent from a dict
ontology_event_from_dict = OntologyEvent.from_dict(ontology_event_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


