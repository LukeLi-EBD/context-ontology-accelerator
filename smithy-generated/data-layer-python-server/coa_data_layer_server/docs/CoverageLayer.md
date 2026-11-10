# CoverageLayer

One of the four answerability layers.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**layer** | **str** | Layer name: &#x60;ontology&#x60; | &#x60;terms&#x60; | &#x60;metrics&#x60; | &#x60;facts&#x60;. | 
**status** | **str** | &#x60;covered&#x60; | &#x60;partial&#x60; | &#x60;missing&#x60; | &#x60;degraded&#x60; | &#x60;unavailable&#x60; | &#x60;not_applicable&#x60;. | 
**coverage** | **float** | Layer coverage in 0..1. Absent when the layer cannot be computed; clients must render that as \&quot;unavailable\&quot;, never as 0. | [optional] 
**matched** | [**List[LayerMatch]**](LayerMatch.md) | Evidence that matched in this layer. Fields are layer-specific: ontology and term matches carry id/label/predicate/source, metrics carry id/label/score, facts carry metricId/status/code/observationRows. | 
**missing** | **List[str]** | Short human-readable descriptions of what this layer lacks. | 

## Example

```python
from coa_data_layer_server.models.coverage_layer import CoverageLayer

# TODO update the JSON string below
json = "{}"
# create an instance of CoverageLayer from a JSON string
coverage_layer_instance = CoverageLayer.from_json(json)
# print the JSON string representation of the object
print(CoverageLayer.to_json())

# convert the object into a dict
coverage_layer_dict = coverage_layer_instance.to_dict()
# create an instance of CoverageLayer from a dict
coverage_layer_from_dict = CoverageLayer.from_dict(coverage_layer_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


