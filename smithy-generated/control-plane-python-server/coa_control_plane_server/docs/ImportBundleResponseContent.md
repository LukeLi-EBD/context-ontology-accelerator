# ImportBundleResponseContent

Result of `ImportBundle`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ok** | **bool** | True when every restored check agrees. | [optional] 
**database** | **str** | Restore database the bundle was loaded into. | [optional] 
**bundle** | **str** | Bundle directory that was imported. | [optional] 
**tbox** | [**BundleTboxRestored**](BundleTboxRestored.md) |  | [optional] 
**tbox_pointer** | [**OntologyPointer**](OntologyPointer.md) |  | [optional] 
**abox_graph** | **str** | A-Box graph the bundle was loaded into. | [optional] 
**checks** | [**List[BundleCheck]**](BundleCheck.md) | Post-import consistency checks. | [optional] 
**ledger** | [**BundleLedger**](BundleLedger.md) |  | [optional] 
**blobs** | [**BundleBlobs**](BundleBlobs.md) |  | [optional] 
**counts** | **object** | Expected row counts from the manifest. | [optional] 
**failed_step** | **str** | Step that failed, when &#x60;ok&#x60; is false. | [optional] 
**error** | **str** | Failure message, when &#x60;ok&#x60; is false. | [optional] 
**provider_code** | **str** | Provider error code, when &#x60;ok&#x60; is false. | [optional] 
**actor** | **str** | Identity that ran the import. | [optional] 

## Example

```python
from coa_control_plane_server.models.import_bundle_response_content import ImportBundleResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ImportBundleResponseContent from a JSON string
import_bundle_response_content_instance = ImportBundleResponseContent.from_json(json)
# print the JSON string representation of the object
print(ImportBundleResponseContent.to_json())

# convert the object into a dict
import_bundle_response_content_dict = import_bundle_response_content_instance.to_dict()
# create an instance of ImportBundleResponseContent from a dict
import_bundle_response_content_from_dict = ImportBundleResponseContent.from_dict(import_bundle_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


