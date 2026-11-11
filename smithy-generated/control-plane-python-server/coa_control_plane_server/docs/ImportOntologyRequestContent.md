# ImportOntologyRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**content** | **str** | Ontology text to parse. | 
**format** | [**OntologyImportFormat**](OntologyImportFormat.md) |  | [optional] 
**change_summary** | **str** | Summary of what the upload changes. | [optional] 
**author** | **str** | Author recorded on the import record. | [optional] 

## Example

```python
from coa_control_plane_server.models.import_ontology_request_content import ImportOntologyRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ImportOntologyRequestContent from a JSON string
import_ontology_request_content_instance = ImportOntologyRequestContent.from_json(json)
# print the JSON string representation of the object
print(ImportOntologyRequestContent.to_json())

# convert the object into a dict
import_ontology_request_content_dict = import_ontology_request_content_instance.to_dict()
# create an instance of ImportOntologyRequestContent from a dict
import_ontology_request_content_from_dict = ImportOntologyRequestContent.from_dict(import_ontology_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


