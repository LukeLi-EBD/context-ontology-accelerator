# BundleBlobs

Blob-store outcome after an import.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**included** | **bool** | True when the bundle carried blobs. | [optional] 
**count** | **float** | Blobs present in the bundle. | [optional] 
**bytes** | **float** | Total blob bytes. | [optional] 
**written** | **float** | Blobs written into the restore target. | [optional] 
**existing** | **float** | Blobs that already existed in the target. | [optional] 

## Example

```python
from coa_control_plane_server.models.bundle_blobs import BundleBlobs

# TODO update the JSON string below
json = "{}"
# create an instance of BundleBlobs from a JSON string
bundle_blobs_instance = BundleBlobs.from_json(json)
# print the JSON string representation of the object
print(BundleBlobs.to_json())

# convert the object into a dict
bundle_blobs_dict = bundle_blobs_instance.to_dict()
# create an instance of BundleBlobs from a dict
bundle_blobs_from_dict = BundleBlobs.from_dict(bundle_blobs_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


