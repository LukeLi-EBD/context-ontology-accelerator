# StartInductionRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**datasource_ids** | **List[str]** | Data source IDs to induct from. The table-based strategies (&#x60;table_to_ontology&#x60;, &#x60;rigor_ontology&#x60;) need at least one; an empty list is rejected with a 400. &#x60;unstructured_lexical_graph&#x60; reads the lexical graph instead and accepts an empty list. &#x60;bridge_to_tables&#x60; runs on an accepted ontology and ignores the list; send an empty one. | 
**ontology_uri_prefix** | **str** | URI prefix for generated ontology classes and properties. For the &#x60;bridge_to_tables&#x60; strategy, the ID of the accepted ontology to bridge (404 if the namespace has no such ontology). | 
**label** | **str** | Human-readable label for this induction run. | [optional] 
**confidence_threshold** | **float** | Confidence threshold for matching against existing ontologies. | [optional] 
**rerank_max_tokens** | **float** | Output-token cap for the ENHANCED-mode LLM grounding rerank. Raise it when a reasoning model truncates its JSON answer (the rerank fails loud naming this knob). Omitted → server default (1000). | [optional] 
**strategy** | [**InductionStrategy**](InductionStrategy.md) |  | [optional] 
**bridge_options** | [**BridgeOptions**](BridgeOptions.md) |  | [optional] 
**grounding_ontology_ids** | **List[str]** | Existing ontology IDs to ground against (reuse existing concepts). | [optional] 
**grounding_mode** | [**GroundingMode**](GroundingMode.md) |  | [optional] 
**graph_arn** | **str** | Caller-selected lexical sources are not supported. A Neptune Analytics graph ARN or graph id returns HTTP 422 with &#x60;&#x60;detail.code&#x60;&#x60; set to &#x60;&#x60;UNSUPPORTED_SOURCE&#x60;&#x60;; the &#x60;&#x60;neptune-db&#x60;&#x60; sentinel names the deployment-configured lexical source, the same as omitting the field. This shape is deprecated since 2026-10-01: Caller-selected lexical sources are not supported; omit this field. | [optional] 
**client_token** | **str** | Optional idempotency token. A retry with the same token and the same parameters within 24 hours returns the original result instead of creating a duplicate; reusing the token with different parameters is rejected with ConflictError (409). | [optional] 

## Example

```python
from coa_control_plane_server.models.start_induction_request_content import StartInductionRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of StartInductionRequestContent from a JSON string
start_induction_request_content_instance = StartInductionRequestContent.from_json(json)
# print the JSON string representation of the object
print(StartInductionRequestContent.to_json())

# convert the object into a dict
start_induction_request_content_dict = start_induction_request_content_instance.to_dict()
# create an instance of StartInductionRequestContent from a dict
start_induction_request_content_from_dict = StartInductionRequestContent.from_dict(start_induction_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


