# BrowseOntologyTreeResponseContent

Class hierarchy, flat class list and property list of the current T-Box.  When nothing is published the server returns an empty `tree`, empty `classes`/`properties`, zero counts and no `pointer`; it does not raise `NotFoundError`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**pointer** | [**OntologyPointer**](OntologyPointer.md) |  | [optional] 
**tree** | [**List[OntologyTreeNode]**](OntologyTreeNode.md) | Nested class tree, roots sorted by label. | 
**classes** | [**List[OntologyClassRef]**](OntologyClassRef.md) | Flat class list, sorted by label. | 
**properties** | [**List[OntologyPropertyRef]**](OntologyPropertyRef.md) | Flat property list, sorted by label. | 
**counts** | [**OntologyBrowseCounts**](OntologyBrowseCounts.md) |  | 

## Example

```python
from coa_control_plane_server.models.browse_ontology_tree_response_content import BrowseOntologyTreeResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of BrowseOntologyTreeResponseContent from a JSON string
browse_ontology_tree_response_content_instance = BrowseOntologyTreeResponseContent.from_json(json)
# print the JSON string representation of the object
print(BrowseOntologyTreeResponseContent.to_json())

# convert the object into a dict
browse_ontology_tree_response_content_dict = browse_ontology_tree_response_content_instance.to_dict()
# create an instance of BrowseOntologyTreeResponseContent from a dict
browse_ontology_tree_response_content_from_dict = BrowseOntologyTreeResponseContent.from_dict(browse_ontology_tree_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


