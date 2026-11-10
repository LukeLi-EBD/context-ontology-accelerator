# MaterializeReasoningRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**profile** | **str** | &#x60;EL&#x60; (default) or &#x60;OWL2EL&#x60;. | [optional] 
**force** | **bool** | Re-run even when the inputs are unchanged. | [optional] 
**abox_graphs** | **List[str]** | A-Box graphs to reason over. Every IRI must be a &#x60;urn:platform:&#x60; graph, so a namespace cannot read another namespace&#39;s graph. When omitted the deployment&#39;s configured A-Box graphs are used. | [optional] 

## Example

```python
from coa_control_plane_server.models.materialize_reasoning_request_content import MaterializeReasoningRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of MaterializeReasoningRequestContent from a JSON string
materialize_reasoning_request_content_instance = MaterializeReasoningRequestContent.from_json(json)
# print the JSON string representation of the object
print(MaterializeReasoningRequestContent.to_json())

# convert the object into a dict
materialize_reasoning_request_content_dict = materialize_reasoning_request_content_instance.to_dict()
# create an instance of MaterializeReasoningRequestContent from a dict
materialize_reasoning_request_content_from_dict = MaterializeReasoningRequestContent.from_dict(materialize_reasoning_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


