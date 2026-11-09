# GraphTraverseResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**entities** | [**List[Entity]**](Entity.md) | Entities reached during traversal. | 
**relationships** | [**List[Relationship]**](Relationship.md) | Relationships traversed. | 
**trace** | [**List[TraceStep]**](TraceStep.md) | Step-by-step trace of the traversal. | 

## Example

```python
from coa_data_layer_server.models.graph_traverse_response_content import GraphTraverseResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GraphTraverseResponseContent from a JSON string
graph_traverse_response_content_instance = GraphTraverseResponseContent.from_json(json)
# print the JSON string representation of the object
print(GraphTraverseResponseContent.to_json())

# convert the object into a dict
graph_traverse_response_content_dict = graph_traverse_response_content_instance.to_dict()
# create an instance of GraphTraverseResponseContent from a dict
graph_traverse_response_content_from_dict = GraphTraverseResponseContent.from_dict(graph_traverse_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


