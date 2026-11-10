# OntologyDiffExamples

Sample triples for each side of the diff.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**added_triples** | [**List[TripleExample]**](TripleExample.md) | Sample of added triples. | 
**removed_triples** | [**List[TripleExample]**](TripleExample.md) | Sample of removed triples. | 

## Example

```python
from coa_control_plane_server.models.ontology_diff_examples import OntologyDiffExamples

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyDiffExamples from a JSON string
ontology_diff_examples_instance = OntologyDiffExamples.from_json(json)
# print the JSON string representation of the object
print(OntologyDiffExamples.to_json())

# convert the object into a dict
ontology_diff_examples_dict = ontology_diff_examples_instance.to_dict()
# create an instance of OntologyDiffExamples from a dict
ontology_diff_examples_from_dict = OntologyDiffExamples.from_dict(ontology_diff_examples_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


