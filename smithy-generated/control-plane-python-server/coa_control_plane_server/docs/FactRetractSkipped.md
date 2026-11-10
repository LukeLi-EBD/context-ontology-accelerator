# FactRetractSkipped

One fact skipped by a batch retract.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fact_id** | **str** | Assertion-row identifier. | 
**reason** | **str** | Why the row was skipped. | 

## Example

```python
from coa_control_plane_server.models.fact_retract_skipped import FactRetractSkipped

# TODO update the JSON string below
json = "{}"
# create an instance of FactRetractSkipped from a JSON string
fact_retract_skipped_instance = FactRetractSkipped.from_json(json)
# print the JSON string representation of the object
print(FactRetractSkipped.to_json())

# convert the object into a dict
fact_retract_skipped_dict = fact_retract_skipped_instance.to_dict()
# create an instance of FactRetractSkipped from a dict
fact_retract_skipped_from_dict = FactRetractSkipped.from_dict(fact_retract_skipped_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


