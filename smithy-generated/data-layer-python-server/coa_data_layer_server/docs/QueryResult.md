# QueryResult

The top-level result of a query: the answering tier, confidence, tabular rows and/or a synthesized answer, the query that ran, supporting content, graph context, and an execution trace.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tier** | **float** | The answering tier that produced this result. | 
**confidence** | [**ConfidenceScore**](ConfidenceScore.md) |  | 
**result_rows** | **List[Dict[str, str]]** | Tabular result rows returned by the query. | [optional] 
**synthesized_answer** | **str** | Natural-language answer synthesized from the results. | [optional] 
**query_used** | **str** | The query that was executed to produce the result. | [optional] 
**sparql_generated** | **str** | The SPARQL query generated for the result, if any. | [optional] 
**supporting_content** | [**List[SupportingContent]**](SupportingContent.md) | Knowledge-base chunks supporting the answer. | [optional] 
**graph_context** | [**GraphContext**](GraphContext.md) |  | [optional] 
**trace** | [**List[TraceStep]**](TraceStep.md) | Step-by-step execution trace of the query. | 
**ontology_version** | **str** | Version of the ontology the query ran against. | [optional] 
**data_sources** | **List[str]** | Identifiers of the data sources that contributed to the result. | [optional] 
**partial** | **bool** | Whether the result is partial (incomplete). | [optional] 
**execution_mode** | **str** | The execution mode that produced this result: \&quot;standard\&quot; or \&quot;deep-reasoning\&quot;. Deep Reasoning is a mode orthogonal to the tier cascade, so a client labels an answer by this field rather than inferring mode from &#x60;tier&#x60; (a Deep Reasoning answer resolves at tier 3 but is not Standard mode&#39;s Tier-3 result). Absent on responses that do not set it. | [optional] 

## Example

```python
from coa_data_layer_server.models.query_result import QueryResult

# TODO update the JSON string below
json = "{}"
# create an instance of QueryResult from a JSON string
query_result_instance = QueryResult.from_json(json)
# print the JSON string representation of the object
print(QueryResult.to_json())

# convert the object into a dict
query_result_dict = query_result_instance.to_dict()
# create an instance of QueryResult from a dict
query_result_from_dict = QueryResult.from_dict(query_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


