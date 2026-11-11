# FactAdjudication

Adjudication summary for one conflict group.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**subject** | **str** | Subject IRI. | 
**predicate** | **str** | Predicate IRI. | 
**event_id** | **float** | Event identifier of the effective decision; absent before any decision. | [optional] 
**action** | **str** | Action of the effective decision; absent before any decision. | [optional] 
**actor** | **str** | Identity that made the effective decision. | [optional] 
**reason** | **str** | Why the effective decision was made. | [optional] 
**at** | **str** | When the effective decision was made (ISO-8601). | 
**status** | **str** | &#x60;in_effect&#x60; when the decision still applies, &#x60;undone&#x60; after an undo. | 
**kept** | **str** | Value kept by a &#x60;keep&#x60; decision. | [optional] 
**values** | **List[str]** | Values the group had when the decision was made. | 
**object** | **str** | Merged value written by a &#x60;merge&#x60; decision. | [optional] 
**undone_by** | [**FactUndoReference**](FactUndoReference.md) |  | [optional] 
**history** | [**List[FactAdjudicationEvent]**](FactAdjudicationEvent.md) | Full adjudication history, oldest first. | 
**effective** | [**FactAdjudicationEffective**](FactAdjudicationEffective.md) |  | 

## Example

```python
from coa_control_plane_server.models.fact_adjudication import FactAdjudication

# TODO update the JSON string below
json = "{}"
# create an instance of FactAdjudication from a JSON string
fact_adjudication_instance = FactAdjudication.from_json(json)
# print the JSON string representation of the object
print(FactAdjudication.to_json())

# convert the object into a dict
fact_adjudication_dict = fact_adjudication_instance.to_dict()
# create an instance of FactAdjudication from a dict
fact_adjudication_from_dict = FactAdjudication.from_dict(fact_adjudication_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


