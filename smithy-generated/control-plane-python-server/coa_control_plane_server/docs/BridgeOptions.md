# BridgeOptions

Switches for one document-to-table bridge run. Every member is optional; an omitted member takes the default named in its description. An unknown member is rejected. The run makes one LLM call per batch of up to 25 columns of each table that has document evidence, plus grounding and embedding calls; `maxTables` caps that one-off cost.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**max_tables** | **float** | Most table classes considered in one run. Default 60. | [optional] 
**concurrency** | **float** | Tables processed in parallel. Default 6. | [optional] 
**dry_run** | **bool** | Compute and report the plan without creating a proposal. Default false. | [optional] 

## Example

```python
from coa_control_plane_server.models.bridge_options import BridgeOptions

# TODO update the JSON string below
json = "{}"
# create an instance of BridgeOptions from a JSON string
bridge_options_instance = BridgeOptions.from_json(json)
# print the JSON string representation of the object
print(BridgeOptions.to_json())

# convert the object into a dict
bridge_options_dict = bridge_options_instance.to_dict()
# create an instance of BridgeOptions from a dict
bridge_options_from_dict = BridgeOptions.from_dict(bridge_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


