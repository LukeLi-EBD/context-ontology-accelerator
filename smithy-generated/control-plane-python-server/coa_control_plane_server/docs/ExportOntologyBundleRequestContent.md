# ExportOntologyBundleRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**out** | **str** | Output directory; the server default when omitted. | [optional] 
**tag** | **str** | Bundle tag; a generated tag when omitted. | [optional] 
**include_blobs** | **bool** | Include the A-Box blob store in the bundle. | [optional] 
**actor** | **str** | Who runs the export. | [optional] 

## Example

```python
from coa_control_plane_server.models.export_ontology_bundle_request_content import ExportOntologyBundleRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ExportOntologyBundleRequestContent from a JSON string
export_ontology_bundle_request_content_instance = ExportOntologyBundleRequestContent.from_json(json)
# print the JSON string representation of the object
print(ExportOntologyBundleRequestContent.to_json())

# convert the object into a dict
export_ontology_bundle_request_content_dict = export_ontology_bundle_request_content_instance.to_dict()
# create an instance of ExportOntologyBundleRequestContent from a dict
export_ontology_bundle_request_content_from_dict = ExportOntologyBundleRequestContent.from_dict(export_ontology_bundle_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


