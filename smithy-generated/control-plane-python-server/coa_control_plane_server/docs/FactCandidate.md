# FactCandidate

One subject-predicate-object candidate extracted from a document chunk.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**candidate_id** | **str** | Identifier assigned at extraction time. | 
**subject** | **str** | Subject IRI or literal label as extracted. | 
**predicate** | **str** | Predicate IRI or label as extracted. | 
**object** | **str** | Object IRI or literal label as extracted. | 
**confidence** | **float** | Extractor confidence in [0, 1]. | 
**status** | [**FactCandidateStatus**](FactCandidateStatus.md) |  | 
**document_id** | **str** | Document the candidate was extracted from. | [optional] 
**chunk_id** | **str** | Chunk the candidate was extracted from. | [optional] 
**evidence** | **str** | Source sentence the candidate was extracted from. | [optional] 

## Example

```python
from coa_control_plane_server.models.fact_candidate import FactCandidate

# TODO update the JSON string below
json = "{}"
# create an instance of FactCandidate from a JSON string
fact_candidate_instance = FactCandidate.from_json(json)
# print the JSON string representation of the object
print(FactCandidate.to_json())

# convert the object into a dict
fact_candidate_dict = fact_candidate_instance.to_dict()
# create an instance of FactCandidate from a dict
fact_candidate_from_dict = FactCandidate.from_dict(fact_candidate_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


