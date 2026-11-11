# InspectOntologyBundleResponseContent

Result of `InspectOntologyBundle`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ok** | **bool** | Always true when the manifest verifies. | 
**path** | **str** | Path that was inspected. | 
**tag** | **str** | Tag recorded in the manifest. | [optional] 
**totals** | **Dict[str, object]** | Counters recorded in a bundle manifest. Values are numbers or nested maps, so they stay free-form rather than being flattened into fixed fields. | [optional] 
**tbox** | **object** | T-Box coordinates recorded in the manifest. | [optional] 
**files** | **float** | Number of files in the bundle. | [optional] 

## Example

```python
from coa_control_plane_server.models.inspect_ontology_bundle_response_content import InspectOntologyBundleResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of InspectOntologyBundleResponseContent from a JSON string
inspect_ontology_bundle_response_content_instance = InspectOntologyBundleResponseContent.from_json(json)
# print the JSON string representation of the object
print(InspectOntologyBundleResponseContent.to_json())

# convert the object into a dict
inspect_ontology_bundle_response_content_dict = inspect_ontology_bundle_response_content_instance.to_dict()
# create an instance of InspectOntologyBundleResponseContent from a dict
inspect_ontology_bundle_response_content_from_dict = InspectOntologyBundleResponseContent.from_dict(inspect_ontology_bundle_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


