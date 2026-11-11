# OntologyImpactInstances

Instance impact of the change.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | **float** | Instances across every A-Box graph.  Not computable when no A-Box graph is configured. Both an absent member and an explicit &#x60;null&#x60; mean exactly that, and the kernel sends &#x60;null&#x60;; neither is &#x60;0&#x60;. A configured A-Box with no instances reports &#x60;0&#x60;. Client generators model this as an optional member (&#x60;?: number&#x60;), so treat &#x60;null&#x60; as a value the field can actually hold at runtime. | [optional] 
**by_class** | [**List[OntologyImpactClassInstances]**](OntologyImpactClassInstances.md) | Per-class counts, one entry per affected class. | 
**source** | **str** | Where the counts came from. | [optional] 
**note** | **str** | Why a count is absent, e.g. &#x60;没有 A-Box 图，实例数不可算；未以 0 代替&#x60;. | [optional] 
**affected_instances** | **float** | Sum of &#x60;byClass[].instances&#x60; over the affected classes; A-Box only, so absent whenever &#x60;total&#x60; is absent. | [optional] 
**graphs** | **List[str]** | A-Box graph IRIs that were scanned; absent when none is configured. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact_instances import OntologyImpactInstances

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactInstances from a JSON string
ontology_impact_instances_instance = OntologyImpactInstances.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactInstances.to_json())

# convert the object into a dict
ontology_impact_instances_dict = ontology_impact_instances_instance.to_dict()
# create an instance of OntologyImpactInstances from a dict
ontology_impact_instances_from_dict = OntologyImpactInstances.from_dict(ontology_impact_instances_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


