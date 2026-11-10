# GapCandidate

A ranked candidate that may close a gap.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Candidate identifier (metric id). | 
**label** | **str** | Human-readable label. | 
**score** | **float** | Match score in 0..1. | 

## Example

```python
from coa_data_layer_server.models.gap_candidate import GapCandidate

# TODO update the JSON string below
json = "{}"
# create an instance of GapCandidate from a JSON string
gap_candidate_instance = GapCandidate.from_json(json)
# print the JSON string representation of the object
print(GapCandidate.to_json())

# convert the object into a dict
gap_candidate_dict = gap_candidate_instance.to_dict()
# create an instance of GapCandidate from a dict
gap_candidate_from_dict = GapCandidate.from_dict(gap_candidate_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


