# GraphTraverseRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**start_uri** | **str** | IRI of the entity to start traversal from. | 
**max_depth** | **float** | Maximum traversal depth from the starting entity. Defaults to 2. Depths above 2 are accepted but currently traverse 2 hops. | [optional] 
**relationship_filter** | **List[str]** | Accepted and validated, but not yet applied: traversal currently follows every relationship. Reserved for restricting traversal to these relationship (predicate) IRIs. | [optional] 
**direction** | [**TraversalDirection**](TraversalDirection.md) |  | [optional] 
**max_results** | **float** | Maximum number of entities to return. Defaults to 100. | [optional] 

## Example

```python
from coa_data_layer_server.models.graph_traverse_request_content import GraphTraverseRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of GraphTraverseRequestContent from a JSON string
graph_traverse_request_content_instance = GraphTraverseRequestContent.from_json(json)
# print the JSON string representation of the object
print(GraphTraverseRequestContent.to_json())

# convert the object into a dict
graph_traverse_request_content_dict = graph_traverse_request_content_instance.to_dict()
# create an instance of GraphTraverseRequestContent from a dict
graph_traverse_request_content_from_dict = GraphTraverseRequestContent.from_dict(graph_traverse_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


