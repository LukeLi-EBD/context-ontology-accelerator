# RunSparqlRequestContent

The namespace and the statement to run.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**sparql** | **str** | SPARQL text: one SELECT or ASK statement. | 

## Example

```python
from coa_data_layer_server.models.run_sparql_request_content import RunSparqlRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RunSparqlRequestContent from a JSON string
run_sparql_request_content_instance = RunSparqlRequestContent.from_json(json)
# print the JSON string representation of the object
print(RunSparqlRequestContent.to_json())

# convert the object into a dict
run_sparql_request_content_dict = run_sparql_request_content_instance.to_dict()
# create an instance of RunSparqlRequestContent from a dict
run_sparql_request_content_from_dict = RunSparqlRequestContent.from_dict(run_sparql_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


