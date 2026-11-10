# LayerMatch

Layer-specific evidence for one match.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Matched identifier (term IRI or metric id). | [optional] 
**label** | **str** | Human-readable label. | [optional] 
**predicate** | **str** | Predicate that produced the match (ontology layer). | [optional] 
**source** | **str** | Source of the label: &#x60;rdfs:label&#x60; or &#x60;skos&#x60;. | [optional] 
**score** | **float** | Match score (metrics layer). | [optional] 
**metric_id** | **str** | Metric this evidence belongs to (facts layer). | [optional] 
**status** | **str** | Fact coverage status for that metric. | [optional] 
**code** | **str** | Stable machine-readable status code. | [optional] 
**observation_rows** | **float** | Number of fact rows backing the metric. | [optional] 
**fact_function** | **str** | Fact function declared by the metric. | [optional] 

## Example

```python
from coa_data_layer_server.models.layer_match import LayerMatch

# TODO update the JSON string below
json = "{}"
# create an instance of LayerMatch from a JSON string
layer_match_instance = LayerMatch.from_json(json)
# print the JSON string representation of the object
print(LayerMatch.to_json())

# convert the object into a dict
layer_match_dict = layer_match_instance.to_dict()
# create an instance of LayerMatch from a dict
layer_match_from_dict = LayerMatch.from_dict(layer_match_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


