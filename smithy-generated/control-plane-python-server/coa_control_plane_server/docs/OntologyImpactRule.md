# OntologyImpactRule

One metric rule that depends on the affected classes or properties.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_id** | **str** | Metric that owns the rule. | 
**rule_id** | **str** | Rule identifier inside the metric&#39;s rule set. | [optional] 
**level** | **str** | Rule severity, as the rule set declares it. | [optional] 
**matched_by** | **str** | &#x60;rule_set_text&#x60; or &#x60;dependent_metric&#x60;. | 
**source** | **str** | Where the rule was read from. | 

## Example

```python
from coa_control_plane_server.models.ontology_impact_rule import OntologyImpactRule

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactRule from a JSON string
ontology_impact_rule_instance = OntologyImpactRule.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactRule.to_json())

# convert the object into a dict
ontology_impact_rule_dict = ontology_impact_rule_instance.to_dict()
# create an instance of OntologyImpactRule from a dict
ontology_impact_rule_from_dict = OntologyImpactRule.from_dict(ontology_impact_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


