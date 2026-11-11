# BundleTboxRestored

T-Box coordinates recorded by an import.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version_id** | **str** | Version the bundle registered. | [optional] 
**content_hash** | **str** | Canonical hash of the restored graph. | [optional] 
**graph** | **str** | Graph IRI the bundle was loaded into. | [optional] 

## Example

```python
from coa_control_plane_server.models.bundle_tbox_restored import BundleTboxRestored

# TODO update the JSON string below
json = "{}"
# create an instance of BundleTboxRestored from a JSON string
bundle_tbox_restored_instance = BundleTboxRestored.from_json(json)
# print the JSON string representation of the object
print(BundleTboxRestored.to_json())

# convert the object into a dict
bundle_tbox_restored_dict = bundle_tbox_restored_instance.to_dict()
# create an instance of BundleTboxRestored from a dict
bundle_tbox_restored_from_dict = BundleTboxRestored.from_dict(bundle_tbox_restored_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


