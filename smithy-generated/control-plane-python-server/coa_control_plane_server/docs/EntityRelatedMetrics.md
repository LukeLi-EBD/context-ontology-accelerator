# EntityRelatedMetrics

Metrics related to the entity, with the match verdict.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | &#x60;matched&#x60;, &#x60;empty&#x60;, or &#x60;unavailable&#x60;. | 
**reason** | **str** | Why no metrics matched, when status is &#x60;empty&#x60; or &#x60;unavailable&#x60;. | [optional] 
**items** | [**List[RelatedMetric]**](RelatedMetric.md) | Related metrics. | 
**match_basis** | **List[str]** | Bases used to match metrics. | 

## Example

```python
from coa_control_plane_server.models.entity_related_metrics import EntityRelatedMetrics

# TODO update the JSON string below
json = "{}"
# create an instance of EntityRelatedMetrics from a JSON string
entity_related_metrics_instance = EntityRelatedMetrics.from_json(json)
# print the JSON string representation of the object
print(EntityRelatedMetrics.to_json())

# convert the object into a dict
entity_related_metrics_dict = entity_related_metrics_instance.to_dict()
# create an instance of EntityRelatedMetrics from a dict
entity_related_metrics_from_dict = EntityRelatedMetrics.from_dict(entity_related_metrics_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


