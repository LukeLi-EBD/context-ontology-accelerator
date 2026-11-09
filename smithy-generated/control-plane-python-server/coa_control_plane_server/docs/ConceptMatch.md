# ConceptMatch

A single concept match result.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_table** | **str** | Source table the match originates from. | 
**source_table_identity** | **str** | Stable data-source-qualified identity for the source table. New structured inductions populate this so same-named tables remain distinguishable; absent on legacy and unstructured matches. | [optional] 
**source_column** | **str** | Source column the match originates from. | 
**matched_class_uri** | **str** | Matched class URI (null if novel). | [optional] 
**matched_ontology_id** | **str** | Ontology ID containing the matched class. | [optional] 
**similarity** | **float** | Similarity score (0.0 to 1.0). | [optional] 
**match_type** | [**MatchType**](MatchType.md) |  | 

## Example

```python
from coa_control_plane_server.models.concept_match import ConceptMatch

# TODO update the JSON string below
json = "{}"
# create an instance of ConceptMatch from a JSON string
concept_match_instance = ConceptMatch.from_json(json)
# print the JSON string representation of the object
print(ConceptMatch.to_json())

# convert the object into a dict
concept_match_dict = concept_match_instance.to_dict()
# create an instance of ConceptMatch from a dict
concept_match_from_dict = ConceptMatch.from_dict(concept_match_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


