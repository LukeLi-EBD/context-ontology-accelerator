# ExportOntologyBundleResponseContent

Result of `ExportOntologyBundle`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ok** | **bool** | Always true on success. | 
**bundle_dir** | **str** | Absolute directory the bundle was written to. | 
**tag** | **str** | Tag recorded in the manifest. | 
**schema_version** | **float** | Manifest schema version. | [optional] 
**generated_at** | **str** | Manifest generation time (ISO-8601). | [optional] 
**tbox** | **object** | T-Box coordinates captured by the bundle. | [optional] 
**totals** | **Dict[str, object]** | Counters recorded in a bundle manifest. Values are numbers or nested maps, so they stay free-form rather than being flattened into fixed fields. | [optional] 
**bytes** | **float** | Total bytes written. | [optional] 
**files** | **float** | Number of files written. | [optional] 
**actor** | **str** | Identity that ran the export. | [optional] 

## Example

```python
from coa_control_plane_server.models.export_ontology_bundle_response_content import ExportOntologyBundleResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ExportOntologyBundleResponseContent from a JSON string
export_ontology_bundle_response_content_instance = ExportOntologyBundleResponseContent.from_json(json)
# print the JSON string representation of the object
print(ExportOntologyBundleResponseContent.to_json())

# convert the object into a dict
export_ontology_bundle_response_content_dict = export_ontology_bundle_response_content_instance.to_dict()
# create an instance of ExportOntologyBundleResponseContent from a dict
export_ontology_bundle_response_content_from_dict = ExportOntologyBundleResponseContent.from_dict(export_ontology_bundle_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


