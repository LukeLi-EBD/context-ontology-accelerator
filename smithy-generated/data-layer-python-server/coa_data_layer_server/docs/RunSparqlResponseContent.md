# RunSparqlResponseContent

One executed statement: its form, the ASK answer, or the SELECT columns and rows.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**form** | **str** | The executed form: &#x60;SELECT&#x60; or &#x60;ASK&#x60;. | 
**answer** | **bool** | The ASK answer; present only when &#x60;form&#x60; is &#x60;ASK&#x60;. | [optional] 
**variables** | **List[str]** | Column names, in the provider&#39;s order (SELECT only). | [optional] 
**rows** | **List[List[str]]** | Rows, each aligned to &#x60;variables&#x60; (SELECT only). | [optional] 
**row_count** | **float** | Rows the provider produced before the 5,000-row display cap (SELECT only). | 
**returned_rows** | **float** | Rows actually returned in &#x60;rows&#x60; (SELECT only; at most 5,000). | 
**truncated** | **bool** | True when the provider produced more than 5,000 rows and &#x60;rows&#x60; was cut. | 
**graph_count** | **float** | Number of namespace graphs the query was confined to. | 
**elapsed_ms** | **float** | Server-side execution time in milliseconds. | [optional] 

## Example

```python
from coa_data_layer_server.models.run_sparql_response_content import RunSparqlResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RunSparqlResponseContent from a JSON string
run_sparql_response_content_instance = RunSparqlResponseContent.from_json(json)
# print the JSON string representation of the object
print(RunSparqlResponseContent.to_json())

# convert the object into a dict
run_sparql_response_content_dict = run_sparql_response_content_instance.to_dict()
# create an instance of RunSparqlResponseContent from a dict
run_sparql_response_content_from_dict = RunSparqlResponseContent.from_dict(run_sparql_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


