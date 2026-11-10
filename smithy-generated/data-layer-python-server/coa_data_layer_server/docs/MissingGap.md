# MissingGap

A gap: what is missing, in which layer, and how to fix it (F79).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**layer** | **str** | Layer the gap belongs to: &#x60;ontology&#x60; | &#x60;terms&#x60; | &#x60;metrics&#x60; | &#x60;facts&#x60;. | 
**code** | **str** | Stable machine-readable code, e.g. &#x60;E_LAYER_ONTOLOGY_GAP&#x60;. | 
**text** | **str** | The question fragment that could not be covered (ontology layer). | [optional] 
**span** | **List[float]** | Inclusive-exclusive [start, end) span of that fragment, when known. | [optional] 
**what** | **str** | What exactly is missing, phrased as an operator action target. | [optional] 
**how_to_fix** | **str** | How to close the gap. | [optional] 
**metric_id** | **str** | Metric this gap belongs to (facts layer). | [optional] 
**nearby_terms** | [**List[NearbyTerm]**](NearbyTerm.md) | Lexically nearby terms that may be the intended concept. | [optional] 
**candidates** | [**List[GapCandidate]**](GapCandidate.md) | Ranked candidates that may close this gap. | [optional] 

## Example

```python
from coa_data_layer_server.models.missing_gap import MissingGap

# TODO update the JSON string below
json = "{}"
# create an instance of MissingGap from a JSON string
missing_gap_instance = MissingGap.from_json(json)
# print the JSON string representation of the object
print(MissingGap.to_json())

# convert the object into a dict
missing_gap_dict = missing_gap_instance.to_dict()
# create an instance of MissingGap from a dict
missing_gap_from_dict = MissingGap.from_dict(missing_gap_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


