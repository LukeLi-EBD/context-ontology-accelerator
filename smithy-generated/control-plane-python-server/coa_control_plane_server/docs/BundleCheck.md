# BundleCheck

One post-import consistency check.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Check name, e.g. &#x60;documents&#x60; or &#x60;vectors&#x60;. | 
**exported** | **object** | Value recorded in the manifest. | [optional] 
**imported** | **object** | Value observed in the restored database. | [optional] 
**ok** | **bool** | True when the two values agree. | 
**detail** | **str** | Explanation when the check failed. | [optional] 

## Example

```python
from coa_control_plane_server.models.bundle_check import BundleCheck

# TODO update the JSON string below
json = "{}"
# create an instance of BundleCheck from a JSON string
bundle_check_instance = BundleCheck.from_json(json)
# print the JSON string representation of the object
print(BundleCheck.to_json())

# convert the object into a dict
bundle_check_dict = bundle_check_instance.to_dict()
# create an instance of BundleCheck from a dict
bundle_check_from_dict = BundleCheck.from_dict(bundle_check_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


