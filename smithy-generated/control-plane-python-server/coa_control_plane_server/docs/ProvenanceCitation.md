# ProvenanceCitation

One citation that resolves a field value.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**kind** | **str** | Citation kind. | 
**ref** | **str** | Citation reference. | [optional] 
**text** | **str** | Text span of the citation. | [optional] 
**document_id** | **str** | Document that contains the citation. | [optional] 
**url** | **str** | Console URL for the citation. | [optional] 

## Example

```python
from coa_control_plane_server.models.provenance_citation import ProvenanceCitation

# TODO update the JSON string below
json = "{}"
# create an instance of ProvenanceCitation from a JSON string
provenance_citation_instance = ProvenanceCitation.from_json(json)
# print the JSON string representation of the object
print(ProvenanceCitation.to_json())

# convert the object into a dict
provenance_citation_dict = provenance_citation_instance.to_dict()
# create an instance of ProvenanceCitation from a dict
provenance_citation_from_dict = ProvenanceCitation.from_dict(provenance_citation_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


