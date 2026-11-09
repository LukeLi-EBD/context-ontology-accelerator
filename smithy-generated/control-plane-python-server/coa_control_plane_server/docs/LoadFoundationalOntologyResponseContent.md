# LoadFoundationalOntologyResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Load status for the foundational ontology. | 
**ontology_id** | **str** | Ontology ID assigned to the loaded foundational ontology. | [optional] 
**class_count** | **float** | Number of classes loaded. | [optional] 
**embedding_count** | **float** | Number of embeddings generated. | [optional] 

## Example

```python
from coa_control_plane_server.models.load_foundational_ontology_response_content import LoadFoundationalOntologyResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of LoadFoundationalOntologyResponseContent from a JSON string
load_foundational_ontology_response_content_instance = LoadFoundationalOntologyResponseContent.from_json(json)
# print the JSON string representation of the object
print(LoadFoundationalOntologyResponseContent.to_json())

# convert the object into a dict
load_foundational_ontology_response_content_dict = load_foundational_ontology_response_content_instance.to_dict()
# create an instance of LoadFoundationalOntologyResponseContent from a dict
load_foundational_ontology_response_content_from_dict = LoadFoundationalOntologyResponseContent.from_dict(load_foundational_ontology_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


