# FactAdjudicationEvent

One event in an adjudication's history.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**event_id** | **float** | Monotonic event identifier. | 
**action** | **str** | Event name (&#x60;keep&#x60;, &#x60;keep_both&#x60;, &#x60;merge&#x60;, &#x60;undo&#x60;). | 
**actor** | **str** | Identity that performed the action. | [optional] 
**reason** | **str** | Why the action was taken. | [optional] 
**at** | **str** | When the event was written (ISO-8601). | 
**payload** | **object** | Event-specific payload. | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_adjudication_event import FactAdjudicationEvent

# TODO update the JSON string below
json = "{}"
# create an instance of FactAdjudicationEvent from a JSON string
fact_adjudication_event_instance = FactAdjudicationEvent.from_json(json)
# print the JSON string representation of the object
print(FactAdjudicationEvent.to_json())

# convert the object into a dict
fact_adjudication_event_dict = fact_adjudication_event_instance.to_dict()
# create an instance of FactAdjudicationEvent from a dict
fact_adjudication_event_from_dict = FactAdjudicationEvent.from_dict(fact_adjudication_event_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


