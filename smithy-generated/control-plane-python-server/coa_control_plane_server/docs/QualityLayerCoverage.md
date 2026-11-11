# QualityLayerCoverage

Citation coverage of one retrieval layer across a single run.  A case counts as covered for a layer when at least one of its citations belongs to that layer's citation kinds. The four layers are `ontology`, `terms`, `metrics` and `facts`; a `chunk` citation is a document hit and is not attributed to any of them.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**layer** | **str** | Layer name: &#x60;ontology&#x60;, &#x60;terms&#x60;, &#x60;metrics&#x60; or &#x60;facts&#x60;. | 
**covered** | **float** | Cases in the run with at least one citation from this layer. | 
**evaluated** | **float** | Cases evaluated in the run. | 
**rate** | **float** | &#x60;covered / evaluated&#x60;, 0..1. | 

## Example

```python
from coa_control_plane_server.models.quality_layer_coverage import QualityLayerCoverage

# TODO update the JSON string below
json = "{}"
# create an instance of QualityLayerCoverage from a JSON string
quality_layer_coverage_instance = QualityLayerCoverage.from_json(json)
# print the JSON string representation of the object
print(QualityLayerCoverage.to_json())

# convert the object into a dict
quality_layer_coverage_dict = quality_layer_coverage_instance.to_dict()
# create an instance of QualityLayerCoverage from a dict
quality_layer_coverage_from_dict = QualityLayerCoverage.from_dict(quality_layer_coverage_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


