# MaterializeReasoningResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | Identifier of the row in &#x60;platform.reasoning_job&#x60;. | 
**mode** | **str** | &#x60;materialize&#x60; or &#x60;rdfs&#x60;. | 
**profile** | **str** | Reasoning profile that was used. | 
**ontology_version** | **str** | Published ontology version the run read. | 
**target_graph** | **str** | Graph the run would replace (and did replace unless skipped). | 
**inferred** | **float** | Triples this run added; 0 when skipped. | 
**skipped** | **bool** | True when the inputs were unchanged and nothing was written. | 
**consistent** | **bool** | Consistency verdict from the reasoner. False fails the job and leaves the target graph untouched. | 
**input_hash** | **str** | Hash of (T-Box, A-Box, profile, mode) used to decide &#x60;skipped&#x60;. | [optional] 
**ms** | **float** | Wall time of the run. | 
**stages** | [**ReasoningStages**](ReasoningStages.md) |  | 
**warnings** | **List[str]** | Non-fatal notes, for example axioms the EL profile ignores. | 

## Example

```python
from coa_control_plane_server.models.materialize_reasoning_response_content import MaterializeReasoningResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of MaterializeReasoningResponseContent from a JSON string
materialize_reasoning_response_content_instance = MaterializeReasoningResponseContent.from_json(json)
# print the JSON string representation of the object
print(MaterializeReasoningResponseContent.to_json())

# convert the object into a dict
materialize_reasoning_response_content_dict = materialize_reasoning_response_content_instance.to_dict()
# create an instance of MaterializeReasoningResponseContent from a dict
materialize_reasoning_response_content_from_dict = MaterializeReasoningResponseContent.from_dict(materialize_reasoning_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


