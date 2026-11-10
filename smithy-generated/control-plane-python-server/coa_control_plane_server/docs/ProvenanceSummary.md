# ProvenanceSummary

Aggregate coverage of the three evidence states.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | **float** | Number of fields. | 
**evidenced** | **float** | Fields with resolved evidence. | 
**inferred** | **float** | Fields backed only by inference. | 
**var_none** | **float** | Fields with no evidence. | 
**with_source_ref** | **float** | Fields with a source reference. | 
**with_prov** | **float** | Fields with a PROV link. | 
**coverage_rate** | **float** | Share of fields that are not &#x60;none&#x60; (0-1). | 

## Example

```python
from coa_control_plane_server.models.provenance_summary import ProvenanceSummary

# TODO update the JSON string below
json = "{}"
# create an instance of ProvenanceSummary from a JSON string
provenance_summary_instance = ProvenanceSummary.from_json(json)
# print the JSON string representation of the object
print(ProvenanceSummary.to_json())

# convert the object into a dict
provenance_summary_dict = provenance_summary_instance.to_dict()
# create an instance of ProvenanceSummary from a dict
provenance_summary_from_dict = ProvenanceSummary.from_dict(provenance_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


