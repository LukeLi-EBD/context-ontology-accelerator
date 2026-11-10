# ImportOntologyResponseContent

Result of `ImportOntology`: the draft row the registry created.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**import_id** | **str** | Import record identifier. | 
**version_id** | **str** | Draft version identifier. | 
**target_namespace** | **str** | Namespace the draft targets. | [optional] 
**author** | **str** | Author recorded on the import. | [optional] 
**change_summary** | **str** | Change summary recorded on the import. | [optional] 
**format** | **str** | Serialisation the content was parsed as. | [optional] 
**triples** | **float** | Triples already in the baseline. | [optional] 
**total_triples** | **float** | Triples in the imported graph. | [optional] 
**classes** | **float** | Distinct OWL classes. | [optional] 
**object_properties** | **float** | Distinct object properties. | [optional] 
**data_properties** | **float** | Distinct datatype properties. | [optional] 
**imports_declared** | **List[str]** | &#x60;owl:imports&#x60; IRIs declared by the source. | [optional] 
**imports_resolved** | **List[object]** | Imports that resolved against the search path. | [optional] 
**unresolved_imports** | **List[object]** | Imports that did not resolve. | [optional] 
**shacl** | [**OntologyShaclResult**](OntologyShaclResult.md) |  | [optional] 
**consistency** | **object** | Consistency check outcome, as the reasoner reported it. | [optional] 
**usable** | **bool** | True when nothing blocks the draft from being proposed. | [optional] 
**reason** | **str** | Provider code explaining why the draft is not usable. | [optional] 
**usable_reasons** | **List[object]** | Every blocker that made the draft unusable. | [optional] 
**published** | **bool** | True when the import was published; always false at this boundary. | [optional] 
**persisted** | **bool** | True when the import record was written. | [optional] 
**slice** | **str** | Implementation slice that produced the result. | [optional] 
**staging_graph** | **str** | Staging graph written by the import. | [optional] 
**source_sha256** | **str** | SHA-256 of the uploaded source. | [optional] 
**created_at** | **str** | Import creation time (ISO-8601). | [optional] 

## Example

```python
from coa_control_plane_server.models.import_ontology_response_content import ImportOntologyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ImportOntologyResponseContent from a JSON string
import_ontology_response_content_instance = ImportOntologyResponseContent.from_json(json)
# print the JSON string representation of the object
print(ImportOntologyResponseContent.to_json())

# convert the object into a dict
import_ontology_response_content_dict = import_ontology_response_content_instance.to_dict()
# create an instance of ImportOntologyResponseContent from a dict
import_ontology_response_content_from_dict = ImportOntologyResponseContent.from_dict(import_ontology_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


