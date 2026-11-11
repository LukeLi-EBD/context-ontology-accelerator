# FactRetractItem

One fact selected by a batch retract.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fact_id** | **str** | Assertion-row identifier. | 
**subject** | **str** | Subject IRI. | 
**predicate** | **str** | Predicate IRI. | 
**object** | **str** | Object value. | 
**object_kind** | **str** | &#x60;iri&#x60; or &#x60;literal&#x60;. | 
**graph** | **str** | Named graph. | 
**candidate_id** | **str** | Extraction candidate that produced the row, when any. | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_retract_item import FactRetractItem

# TODO update the JSON string below
json = "{}"
# create an instance of FactRetractItem from a JSON string
fact_retract_item_instance = FactRetractItem.from_json(json)
# print the JSON string representation of the object
print(FactRetractItem.to_json())

# convert the object into a dict
fact_retract_item_dict = fact_retract_item_instance.to_dict()
# create an instance of FactRetractItem from a dict
fact_retract_item_from_dict = FactRetractItem.from_dict(fact_retract_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


