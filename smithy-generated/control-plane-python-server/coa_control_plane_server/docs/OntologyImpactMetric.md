# OntologyImpactMetric

One metric that depends on the affected classes or properties.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_id** | **str** | Metric identifier. | 
**name** | **str** | Metric display name. | [optional] 
**matched_by** | **List[str]** | Tokens or binding paths that matched, e.g. &#x60;text:invoice&#x60; or &#x60;binding:fact_x.invoice_no&#x60;. | 
**source** | **str** | Registries the match came from. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_metric import OntologyImpactMetric

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactMetric from a JSON string
ontology_impact_metric_instance = OntologyImpactMetric.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactMetric.to_json())

# convert the object into a dict
ontology_impact_metric_dict = ontology_impact_metric_instance.to_dict()
# create an instance of OntologyImpactMetric from a dict
ontology_impact_metric_from_dict = OntologyImpactMetric.from_dict(ontology_impact_metric_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


