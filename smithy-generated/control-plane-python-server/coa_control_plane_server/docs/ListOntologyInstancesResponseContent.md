# ListOntologyInstancesResponseContent

Instances of one class.  An unknown class, or an empty current graph, returns `items: []`, `total: 0` and no `pointer`; it is an empty result, not an error.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_class** | **str** | Class IRI that was queried. | 
**items** | [**List[OntologyInstanceRef]**](OntologyInstanceRef.md) | Instances in T-Box order, capped by &#x60;limit&#x60;. | 
**total** | **float** | Total instances of the class, before &#x60;limit&#x60; was applied. | 
**limit** | **float** | Page size that was applied (server default 20). | 
**offset** | **float** | Offset that was applied (server default 0). | 
**pointer** | [**OntologyPointer**](OntologyPointer.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.list_ontology_instances_response_content import ListOntologyInstancesResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListOntologyInstancesResponseContent from a JSON string
list_ontology_instances_response_content_instance = ListOntologyInstancesResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListOntologyInstancesResponseContent.to_json())

# convert the object into a dict
list_ontology_instances_response_content_dict = list_ontology_instances_response_content_instance.to_dict()
# create an instance of ListOntologyInstancesResponseContent from a dict
list_ontology_instances_response_content_from_dict = ListOntologyInstancesResponseContent.from_dict(list_ontology_instances_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


