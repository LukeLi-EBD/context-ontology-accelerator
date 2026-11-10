# FactSource

Provenance attached to an assertion row.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**kind** | **str** | Source family: &#x60;document&#x60;, &#x60;table&#x60;, &#x60;manual&#x60;, or &#x60;merge&#x60;. | [optional] 
**document_id** | **str** | Document that produced the row, when any. | [optional] 
**run_id** | **str** | Ingestion run that produced the row, when any. | [optional] 
**candidate_id** | **str** | Extraction candidate that produced the row, when any. | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_source import FactSource

# TODO update the JSON string below
json = "{}"
# create an instance of FactSource from a JSON string
fact_source_instance = FactSource.from_json(json)
# print the JSON string representation of the object
print(FactSource.to_json())

# convert the object into a dict
fact_source_dict = fact_source_instance.to_dict()
# create an instance of FactSource from a dict
fact_source_from_dict = FactSource.from_dict(fact_source_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


