# OntologyRecord

Summary of an ontology in the namespace registry.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ontology_id** | **str** | Unique identifier of the ontology within the namespace. | 
**uri** | **str** | Canonical IRI of the ontology. | 
**title** | **str** | Human-readable display title. | [optional] 
**description** | **str** | Human-readable description of the ontology. | [optional] 
**ontology_type** | **str** | Category of the ontology (foundational, induced, or user_created). | [optional] 
**parse_status** | **str** | Ingest lifecycle marker set by the async parse/embed worker: \&quot;pending\&quot; while ingesting, \&quot;ok\&quot; once parsed, \&quot;parse_error\&quot; on failure. Absent on legacy rows persisted before this field existed, for which a positive embeddingCount means the ingest completed. | [optional] 
**status** | **str** | Lifecycle status of the registry row. Set to \&quot;deleting\&quot; while an async ontology delete tears down its graph + embeddings (the row stays listed as \&quot;Delete in progress\&quot; until teardown completes, then is removed). Absent for normal, fully-materialized ontologies. | [optional] 
**delete_error** | **str** | Set when an async delete&#39;s teardown failed (graph/embedding hard gate), leaving the row in status \&quot;deleting\&quot;. Lets a client distinguish a stuck delete (re-issue DELETE to retry) from one still in progress. Cleared when a fresh delete starts; absent otherwise. | [optional] 
**format** | **str** | Serialization format of the source file (e.g. turtle, rdfxml, jsonld). | [optional] 
**domain_tags** | **List[str]** | Domain tags used to categorize and filter the ontology. | [optional] 
**class_count** | **float** | Number of classes in the ontology. | [optional] 
**property_count** | **float** | Number of properties in the ontology. | [optional] 
**axiom_count** | **float** | Number of axioms in the ontology. | [optional] 
**embedding_count** | **float** | Number of vector embeddings generated for the ontology. | [optional] 
**graph_uri** | **str** | IRI of the named graph holding the ontology&#39;s triples. | [optional] 
**created_at** | **str** | Creation timestamp of the registry row. | [optional] 
**updated_at** | **str** | Last-updated timestamp of the registry row. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_record import OntologyRecord

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyRecord from a JSON string
ontology_record_instance = OntologyRecord.from_json(json)
# print the JSON string representation of the object
print(OntologyRecord.to_json())

# convert the object into a dict
ontology_record_dict = ontology_record_instance.to_dict()
# create an instance of OntologyRecord from a dict
ontology_record_from_dict = OntologyRecord.from_dict(ontology_record_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


