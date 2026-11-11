# OntologyImpactVerification

Independent recount of a sample of the affected class counts.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**sampled** | [**List[OntologyImpactSample]**](OntologyImpactSample.md) | Classes that were recounted. | 
**consistent** | **bool** | True when every sampled class agreed.  Not computable when there is no A-Box graph, or when nothing was sampled. Both an absent member and an explicit &#x60;null&#x60; mean \&quot;cannot be computed\&quot;, and the kernel sends &#x60;null&#x60;; neither is &#x60;false&#x60;. Client generators model this as an optional member (&#x60;?: boolean&#x60;), so treat &#x60;null&#x60; as a value the field can actually hold at runtime. | [optional] 
**reason** | **str** | Why no sample was taken, or which class disagreed. | [optional] 
**source** | **str** | Recount method, e.g. &#x60;独立 SPARQL 重算（逐类 COUNT DISTINCT）&#x60;. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_impact_verification import OntologyImpactVerification

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyImpactVerification from a JSON string
ontology_impact_verification_instance = OntologyImpactVerification.from_json(json)
# print the JSON string representation of the object
print(OntologyImpactVerification.to_json())

# convert the object into a dict
ontology_impact_verification_dict = ontology_impact_verification_instance.to_dict()
# create an instance of OntologyImpactVerification from a dict
ontology_impact_verification_from_dict = OntologyImpactVerification.from_dict(ontology_impact_verification_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


