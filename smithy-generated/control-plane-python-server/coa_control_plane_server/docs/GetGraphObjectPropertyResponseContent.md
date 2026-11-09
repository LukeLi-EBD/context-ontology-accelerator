# GetGraphObjectPropertyResponseContent

A node in the ontology graph — a class, property, or individual — with its IRI, kind, namespace, associated labels/comments, and outgoing edges.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | IRI of the vertex. | 
**kind** | **str** | Vertex kind (class, object-property, datatype-property, etc.). | 
**namespace** | **str** | Namespace the vertex belongs to. | 
**types** | **List[str]** | RDF types (rdf:type) declared on the vertex. | [optional] 
**labels** | **List[str]** | Human-readable labels (rdfs:label) of the vertex. | [optional] 
**comments** | **List[str]** | Descriptive comments (rdfs:comment) on the vertex. | [optional] 
**alt_labels** | **List[str]** | Alternative labels (skos:altLabel) — carries source synonyms curated during enrichment and emitted onto the induced class/property. | [optional] 
**graph_uris** | **List[str]** | IRIs of the named graphs the vertex appears in. | [optional] 
**is_mapped** | **bool** | Whether this vertex carries the &#x60;&#x60;coa:isMapped&#x60;&#x60; marker — i.e. it is backed by an R2RML mapping and therefore answerable by the structured Tier-2 (NL→SPARQL / NL→SQL) path. Structured / table-backed classes are true; unstructured-induced and foundational classes are false (the marker is absent). Derived from the top-level &#x60;&#x60;coa:isMapped&#x60;&#x60; triple and excluded from &#x60;&#x60;edges&#x60;&#x60;. | [optional] 
**superseded** | **Dict[str, List[str]]** | Retired annotation literals keyed by kind (&#x60;&#x60;comments&#x60;&#x60; / &#x60;&#x60;definitions&#x60;&#x60; / &#x60;&#x60;altLabels&#x60;&#x60; / &#x60;&#x60;glossaryTerms&#x60;&#x60; / &#x60;&#x60;tags&#x60;&#x60;). See &#x60;&#x60;GraphVertex.superseded&#x60;&#x60;. | [optional] 
**edges** | [**List[GraphEdge]**](GraphEdge.md) | Outgoing relationship edges from this vertex. | [optional] 

## Example

```python
from coa_control_plane_server.models.get_graph_object_property_response_content import GetGraphObjectPropertyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetGraphObjectPropertyResponseContent from a JSON string
get_graph_object_property_response_content_instance = GetGraphObjectPropertyResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetGraphObjectPropertyResponseContent.to_json())

# convert the object into a dict
get_graph_object_property_response_content_dict = get_graph_object_property_response_content_instance.to_dict()
# create an instance of GetGraphObjectPropertyResponseContent from a dict
get_graph_object_property_response_content_from_dict = GetGraphObjectPropertyResponseContent.from_dict(get_graph_object_property_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


