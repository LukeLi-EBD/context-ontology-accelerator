# BundleLedger

Ledger counters and chain verdict after an import.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**events** | **float** | Fact events restored. | [optional] 
**facts** | **float** | Fact assertions restored. | [optional] 
**chain** | **bool** | True when the restored fact-event chain verifies. | [optional] 

## Example

```python
from coa_control_plane_server.models.bundle_ledger import BundleLedger

# TODO update the JSON string below
json = "{}"
# create an instance of BundleLedger from a JSON string
bundle_ledger_instance = BundleLedger.from_json(json)
# print the JSON string representation of the object
print(BundleLedger.to_json())

# convert the object into a dict
bundle_ledger_dict = bundle_ledger_instance.to_dict()
# create an instance of BundleLedger from a dict
bundle_ledger_from_dict = BundleLedger.from_dict(bundle_ledger_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


