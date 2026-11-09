# FoundationalOntologySummary

A foundational (reference) ontology available to ground induction against, identified by its key and title, with an optional description, URI, and domain tags.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**key** | **str** | Catalog key identifying the foundational ontology. | 
**title** | **str** | Display title of the foundational ontology. | 
**description** | **str** | Short description of the ontology&#39;s scope. | [optional] 
**uri** | **str** | Canonical URI of the foundational ontology. | [optional] 
**domain_tags** | **List[str]** | Domain tags categorizing the ontology. | [optional] 

## Example

```python
from coa_control_plane_server.models.foundational_ontology_summary import FoundationalOntologySummary

# TODO update the JSON string below
json = "{}"
# create an instance of FoundationalOntologySummary from a JSON string
foundational_ontology_summary_instance = FoundationalOntologySummary.from_json(json)
# print the JSON string representation of the object
print(FoundationalOntologySummary.to_json())

# convert the object into a dict
foundational_ontology_summary_dict = foundational_ontology_summary_instance.to_dict()
# create an instance of FoundationalOntologySummary from a dict
foundational_ontology_summary_from_dict = FoundationalOntologySummary.from_dict(foundational_ontology_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


