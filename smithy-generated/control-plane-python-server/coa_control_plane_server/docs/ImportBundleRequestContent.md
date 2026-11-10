# ImportBundleRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bundle_ref** | **str** | Bundle directory to restore. | 
**database** | **str** | Restore database; defaults to &#x60;platform_restore_test&#x60; when omitted. | [optional] 
**replace** | **bool** | Drop and recreate the restore database before loading. | [optional] 
**keep_db_on_failure** | **bool** | Keep the restore database when a step fails, for inspection. | [optional] 
**actor** | **str** | Who runs the restore. | [optional] 

## Example

```python
from coa_control_plane_server.models.import_bundle_request_content import ImportBundleRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ImportBundleRequestContent from a JSON string
import_bundle_request_content_instance = ImportBundleRequestContent.from_json(json)
# print the JSON string representation of the object
print(ImportBundleRequestContent.to_json())

# convert the object into a dict
import_bundle_request_content_dict = import_bundle_request_content_instance.to_dict()
# create an instance of ImportBundleRequestContent from a dict
import_bundle_request_content_from_dict = ImportBundleRequestContent.from_dict(import_bundle_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


