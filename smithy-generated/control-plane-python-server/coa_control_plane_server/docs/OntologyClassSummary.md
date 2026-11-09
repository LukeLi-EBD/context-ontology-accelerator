# OntologyClassSummary

One class persisted in an ontology's named graph.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | IRI of the class. | 
**label** | **str** | Human-readable label (rdfs:label) of the class. | [optional] 
**comment** | **str** | Descriptive comment (rdfs:comment) on the class. | [optional] 
**grounded_to** | **str** | IRI of the previously-loaded class this class was grounded to (coa:groundedTo / skos:exactMatch / skos:closeMatch). Absent when the class is novel (net-new this induction). | [optional] 
**match_type** | **str** | \&quot;exact\&quot; or \&quot;close\&quot; when grounded via a SKOS mapping; otherwise absent. | [optional] 
**sub_class_of** | **List[str]** | IRIs of this class&#39;s direct super-classes (&#x60;&#x60;rdfs:subClassOf&#x60;&#x60;). Lets a caller reconstruct the taxonomy (roots + parent/child edges) from the overview alone, without an N-per-class vertex fan-out. Empty/absent for a top-level class with no loaded parent. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_class_summary import OntologyClassSummary

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyClassSummary from a JSON string
ontology_class_summary_instance = OntologyClassSummary.from_json(json)
# print the JSON string representation of the object
print(OntologyClassSummary.to_json())

# convert the object into a dict
ontology_class_summary_dict = ontology_class_summary_instance.to_dict()
# create an instance of OntologyClassSummary from a dict
ontology_class_summary_from_dict = OntologyClassSummary.from_dict(ontology_class_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


