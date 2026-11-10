# FactEvent

One entry in a fact's hash-chained event history.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**event_id** | **float** | Monotonic event identifier within the ledger. | 
**fact_id** | **str** | Fact the event belongs to. | 
**action** | **str** | Event name, e.g. &#x60;assert&#x60;, &#x60;retract&#x60;, &#x60;restore&#x60;, &#x60;merge&#x60;, &#x60;undo&#x60;. | 
**actor** | **str** | Identity that performed the action. | [optional] 
**reason** | **str** | Why the action was taken. | [optional] 
**batch_id** | **str** | Batch identifier shared by a bulk operation. | [optional] 
**payload** | **object** | Event-specific payload written by the ledger. | [optional] 
**prev_event** | **float** | Previous event in the hash chain; absent for the first event. | [optional] 
**hash** | **str** | Hash of this event, chained from &#x60;prevEvent&#x60;. | [optional] 
**created_at** | **str** | When the event was written (ISO-8601). | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_event import FactEvent

# TODO update the JSON string below
json = "{}"
# create an instance of FactEvent from a JSON string
fact_event_instance = FactEvent.from_json(json)
# print the JSON string representation of the object
print(FactEvent.to_json())

# convert the object into a dict
fact_event_dict = fact_event_instance.to_dict()
# create an instance of FactEvent from a dict
fact_event_from_dict = FactEvent.from_dict(fact_event_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


