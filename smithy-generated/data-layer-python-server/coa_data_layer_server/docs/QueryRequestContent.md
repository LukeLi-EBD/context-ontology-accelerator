# QueryRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** | Natural-language question to answer. | 
**execute** | **bool** | Whether to execute the generated query (versus translate only). | [optional] 
**tier_override** | **float** | Pin resolution to a specific tier (1, 2 or 3), bypassing automatic routing. | [optional] 
**mode** | [**QueryMode**](QueryMode.md) |  | [optional] 
**strategy** | [**QueryStrategy**](QueryStrategy.md) |  | [optional] 
**dimensions** | [**List[DimensionFilter]**](DimensionFilter.md) | Dimension filters to constrain the query. | [optional] 
**timeout_ms** | **float** | Maximum time to wait for the query, in milliseconds. A caller may narrow the service&#39;s own REST budget (29,000 ms) but not widen it. | [optional] 
**include_supporting** | **bool** | Whether to include supporting content in the response. When false, &#x60;supportingContent&#x60; and the &#x60;supportingStatements&#x60; property of each &#x60;graphContext&#x60; entity are omitted; the entities and relationships are still returned. | [optional] 
**include_debug_info** | **bool** | When true, include the generated SQL (&#x60;queryUsed&#x60;) and SPARQL (&#x60;sparqlGenerated&#x60;) in the response for debugging and observability. Defaults to false; when unset or false, both fields are omitted.  **Security:** these fields expose internal schema (table and column names, joins), so the flag is honoured only for a caller who already administers that schema: a platform admin, or a namespace owner, maintainer or data steward of the queried namespace. For any other caller the request still succeeds, but both fields are omitted as if the flag were false. | [optional] 
**max_results** | **float** | Maximum number of result rows to return. | [optional] 

## Example

```python
from coa_data_layer_server.models.query_request_content import QueryRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of QueryRequestContent from a JSON string
query_request_content_instance = QueryRequestContent.from_json(json)
# print the JSON string representation of the object
print(QueryRequestContent.to_json())

# convert the object into a dict
query_request_content_dict = query_request_content_instance.to_dict()
# create an instance of QueryRequestContent from a dict
query_request_content_from_dict = QueryRequestContent.from_dict(query_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


