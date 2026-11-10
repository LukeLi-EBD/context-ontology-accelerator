# GraphStatement

One RDF statement (triple) in a namespace's named graphs.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**graph** | **str** | Named graph the statement lives in. | 
**subject** | **str** | Subject IRI. | 
**predicate** | **str** | Predicate IRI. | 
**object** | **str** | Object term: an IRI, or the lexical form of a literal. | 

## Example

```python
from coa_control_plane_server.models.graph_statement import GraphStatement

# TODO update the JSON string below
json = "{}"
# create an instance of GraphStatement from a JSON string
graph_statement_instance = GraphStatement.from_json(json)
# print the JSON string representation of the object
print(GraphStatement.to_json())

# convert the object into a dict
graph_statement_dict = graph_statement_instance.to_dict()
# create an instance of GraphStatement from a dict
graph_statement_from_dict = GraphStatement.from_dict(graph_statement_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


