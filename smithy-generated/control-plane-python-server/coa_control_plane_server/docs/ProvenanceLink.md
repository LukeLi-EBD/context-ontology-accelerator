# ProvenanceLink

One resolution link attached to a provenance field.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**kind** | **str** | Link kind: &#x60;source_ref&#x60;, &#x60;fact&#x60;, &#x60;fact_binding&#x60;, or &#x60;prov&#x60;. | 
**ref** | **str** | Referenced identifier. | [optional] 
**url** | **str** | Console URL for the reference. | [optional] 
**document_id** | **str** | Document that owns the reference, when any. | [optional] 

## Example

```python
from coa_control_plane_server.models.provenance_link import ProvenanceLink

# TODO update the JSON string below
json = "{}"
# create an instance of ProvenanceLink from a JSON string
provenance_link_instance = ProvenanceLink.from_json(json)
# print the JSON string representation of the object
print(ProvenanceLink.to_json())

# convert the object into a dict
provenance_link_dict = provenance_link_instance.to_dict()
# create an instance of ProvenanceLink from a dict
provenance_link_from_dict = ProvenanceLink.from_dict(provenance_link_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


