# PublishOntologyRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version_id** | **str** | Version to publish. | 
**proposal_id** | **str** | Proposal that authorises this publish. | [optional] 
**expected_version_id** | **str** | Optimistic-concurrency guard: the pointer must still select this version, otherwise the publish fails closed. | [optional] 
**acknowledge_breaking** | **bool** | Accept breaking changes recorded in the diff. | [optional] 
**publish_existing** | **bool** | Re-activate an already registered version instead of staging a new one. | [optional] 
**plan_only** | **bool** | Run the gates and return the plan without writing anything. | [optional] 
**actor** | **str** | Who publishes. | [optional] 
**reason** | **str** | Reason recorded on the publish. | [optional] 

## Example

```python
from coa_control_plane_server.models.publish_ontology_request_content import PublishOntologyRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of PublishOntologyRequestContent from a JSON string
publish_ontology_request_content_instance = PublishOntologyRequestContent.from_json(json)
# print the JSON string representation of the object
print(PublishOntologyRequestContent.to_json())

# convert the object into a dict
publish_ontology_request_content_dict = publish_ontology_request_content_instance.to_dict()
# create an instance of PublishOntologyRequestContent from a dict
publish_ontology_request_content_from_dict = PublishOntologyRequestContent.from_dict(publish_ontology_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


