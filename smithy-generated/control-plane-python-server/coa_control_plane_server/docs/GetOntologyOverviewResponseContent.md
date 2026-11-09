# GetOntologyOverviewResponseContent

Everything persisted in one ontology's named graph, grouped for display. Read from the graph store (not the registry), so it reflects the triples that actually landed in the knowledge graph.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ontology_id** | **str** | Identifier of the ontology. | 
**namespace** | **str** | Namespace the ontology belongs to. | 
**graph_uri** | **str** | IRI of the named graph holding the ontology&#39;s triples. | [optional] 
**classes** | [**List[OntologyClassSummary]**](OntologyClassSummary.md) | Classes persisted in the ontology&#39;s named graph. | [optional] 
**object_properties** | [**List[OntologyPropertySummary]**](OntologyPropertySummary.md) | Object properties — relationships between classes (domain → range class). | [optional] 
**datatype_properties** | [**List[OntologyPropertySummary]**](OntologyPropertySummary.md) | Datatype properties — attributes of a class with a literal range. | [optional] 
**total_classes** | **float** | Total number of classes in the ontology (independent of limit/offset), so a client can show the true count while rendering one page. | [optional] 
**total_object_properties** | **float** | Total number of object properties in the ontology (independent of limit/offset). | [optional] 
**total_datatype_properties** | **float** | Total number of datatype properties in the ontology (independent of limit/offset). | [optional] 

## Example

```python
from coa_control_plane_server.models.get_ontology_overview_response_content import GetOntologyOverviewResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOntologyOverviewResponseContent from a JSON string
get_ontology_overview_response_content_instance = GetOntologyOverviewResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetOntologyOverviewResponseContent.to_json())

# convert the object into a dict
get_ontology_overview_response_content_dict = get_ontology_overview_response_content_instance.to_dict()
# create an instance of GetOntologyOverviewResponseContent from a dict
get_ontology_overview_response_content_from_dict = GetOntologyOverviewResponseContent.from_dict(get_ontology_overview_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


