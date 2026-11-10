# RestoreFactResponseContent

One assertion row as returned by the ledger.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fact_id** | **str** | Stable assertion-row identifier. | 
**subject** | **str** | Subject IRI. | 
**predicate** | **str** | Predicate IRI. | 
**object** | [**FactObject**](FactObject.md) |  | 
**graph** | **str** | Named graph the assertion belongs to. | 
**state** | [**FactState**](FactState.md) |  | 
**source** | [**FactSource**](FactSource.md) |  | [optional] 
**asserted_at** | **str** | When the row was first asserted (ISO-8601). | [optional] 
**retracted_at** | **str** | When the row was retracted (ISO-8601); absent while active. | [optional] 
**retract_reason** | **str** | Reason recorded on retraction. | [optional] 
**accepted_conflict** | **bool** | True when the caller accepted the conflict without picking a value. | [optional] 
**resolution** | **str** | Adjudication applied to the row: &#x60;keep&#x60;, &#x60;keep_both&#x60;, or &#x60;merge&#x60;. | [optional] 
**resolved_by** | **str** | Identity that adjudicated the conflict. | [optional] 
**resolved_at** | **str** | When the conflict was adjudicated (ISO-8601). | [optional] 
**superseded_by** | **str** | Row that superseded this one after a merge. | [optional] 
**merged_from** | **List[str]** | Rows merged into this one. | [optional] 
**conflict** | **bool** | True when the (subject, predicate) group currently has a conflict. | [optional] 
**duplicate** | **bool** | True when an identical assertion row already existed and was reused by &#x60;AssertFact&#x60;; absent on reads. | [optional] 
**events** | [**List[FactEvent]**](FactEvent.md) | Event history, present only on &#x60;GetFact&#x60; with events requested. | [optional] 

## Example

```python
from coa_control_plane_server.models.restore_fact_response_content import RestoreFactResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RestoreFactResponseContent from a JSON string
restore_fact_response_content_instance = RestoreFactResponseContent.from_json(json)
# print the JSON string representation of the object
print(RestoreFactResponseContent.to_json())

# convert the object into a dict
restore_fact_response_content_dict = restore_fact_response_content_instance.to_dict()
# create an instance of RestoreFactResponseContent from a dict
restore_fact_response_content_from_dict = RestoreFactResponseContent.from_dict(restore_fact_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


