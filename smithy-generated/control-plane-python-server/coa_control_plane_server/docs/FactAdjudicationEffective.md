# FactAdjudicationEffective

Effective state of a conflict group after replaying its adjudications.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**active_count** | **float** | Number of active rows in the group. | 
**values** | **List[str]** | Values still active. | 
**conflict** | **bool** | True when the active values still conflict. | 
**accepted_conflict** | **bool** | True when the conflict was explicitly accepted. | 

## Example

```python
from coa_control_plane_server.models.fact_adjudication_effective import FactAdjudicationEffective

# TODO update the JSON string below
json = "{}"
# create an instance of FactAdjudicationEffective from a JSON string
fact_adjudication_effective_instance = FactAdjudicationEffective.from_json(json)
# print the JSON string representation of the object
print(FactAdjudicationEffective.to_json())

# convert the object into a dict
fact_adjudication_effective_dict = fact_adjudication_effective_instance.to_dict()
# create an instance of FactAdjudicationEffective from a dict
fact_adjudication_effective_from_dict = FactAdjudicationEffective.from_dict(fact_adjudication_effective_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


