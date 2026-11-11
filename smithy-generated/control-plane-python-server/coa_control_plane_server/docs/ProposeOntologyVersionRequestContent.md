# ProposeOntologyVersionRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version_id** | **str** | Draft version the proposal is about. | 
**rationale** | **str** | Why the draft should be published; also used as the change summary. | 
**against_version** | **str** | Baseline to diff against; the current pointer when omitted. | [optional] 
**actor** | **str** | Who files the proposal. | [optional] 

## Example

```python
from coa_control_plane_server.models.propose_ontology_version_request_content import ProposeOntologyVersionRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ProposeOntologyVersionRequestContent from a JSON string
propose_ontology_version_request_content_instance = ProposeOntologyVersionRequestContent.from_json(json)
# print the JSON string representation of the object
print(ProposeOntologyVersionRequestContent.to_json())

# convert the object into a dict
propose_ontology_version_request_content_dict = propose_ontology_version_request_content_instance.to_dict()
# create an instance of ProposeOntologyVersionRequestContent from a dict
propose_ontology_version_request_content_from_dict = ProposeOntologyVersionRequestContent.from_dict(propose_ontology_version_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


