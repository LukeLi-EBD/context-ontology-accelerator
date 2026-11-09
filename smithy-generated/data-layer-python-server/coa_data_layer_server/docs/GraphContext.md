# GraphContext

Graph context accompanying an answer: the entities and relationships that were traversed or cited.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**entities** | [**List[Entity]**](Entity.md) | Entities traversed or cited for the answer. Bounded to 200 entities per response; a traversal that reached more is reported through &#x60;metadata.degradedSources&#x60; and the processing trace. | [optional] 
**relationships** | [**List[Relationship]**](Relationship.md) | Relationships traversed or cited for the answer. Bounded to 500 relationships per response; a traversal that reached more is reported through &#x60;metadata.degradedSources&#x60; and the processing trace. A relationship the graph carries without a predicate identifier cannot be represented (see &#x60;predicateUri&#x60;) and is reported the same way, so an empty list is never ambiguous between \&quot;none found\&quot; and \&quot;all discarded\&quot;. | [optional] 

## Example

```python
from coa_data_layer_server.models.graph_context import GraphContext

# TODO update the JSON string below
json = "{}"
# create an instance of GraphContext from a JSON string
graph_context_instance = GraphContext.from_json(json)
# print the JSON string representation of the object
print(GraphContext.to_json())

# convert the object into a dict
graph_context_dict = graph_context_instance.to_dict()
# create an instance of GraphContext from a dict
graph_context_from_dict = GraphContext.from_dict(graph_context_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


