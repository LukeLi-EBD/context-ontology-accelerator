# OntologyTreeNode

One class node of the nested tree.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Class IRI. | 
**label** | **str** | Display label. | 
**parents** | **List[str]** | Superclass IRIs; empty for a root class. | [optional] 
**children** | [**List[OntologyTreeNode]**](OntologyTreeNode.md) | Child nodes, sorted by label. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_tree_node import OntologyTreeNode

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyTreeNode from a JSON string
ontology_tree_node_instance = OntologyTreeNode.from_json(json)
# print the JSON string representation of the object
print(OntologyTreeNode.to_json())

# convert the object into a dict
ontology_tree_node_dict = ontology_tree_node_instance.to_dict()
# create an instance of OntologyTreeNode from a dict
ontology_tree_node_from_dict = OntologyTreeNode.from_dict(ontology_tree_node_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


