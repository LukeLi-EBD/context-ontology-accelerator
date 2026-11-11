# OntologyBreakingItem

One element that makes a diff breaking.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**kind** | **str** | Kind: &#x60;class_removed&#x60;, &#x60;property_removed&#x60;, &#x60;domain_narrowed&#x60;, &#x60;range_narrowed&#x60;, or &#x60;property_became_required&#x60;. | 
**iri** | **str** | IRI of the affected class or property; absent for domain/range changes. | [optional] 
**var_property** | **str** | Property IRI for domain/range changes. | [optional] 
**var_from** | **List[str]** | Values before the change. | [optional] 
**to** | **List[str]** | Values after the change. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_breaking_item import OntologyBreakingItem

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyBreakingItem from a JSON string
ontology_breaking_item_instance = OntologyBreakingItem.from_json(json)
# print the JSON string representation of the object
print(OntologyBreakingItem.to_json())

# convert the object into a dict
ontology_breaking_item_dict = ontology_breaking_item_instance.to_dict()
# create an instance of OntologyBreakingItem from a dict
ontology_breaking_item_from_dict = OntologyBreakingItem.from_dict(ontology_breaking_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


