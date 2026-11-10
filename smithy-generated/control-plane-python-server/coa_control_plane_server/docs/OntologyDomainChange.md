# OntologyDomainChange

Domain or range values before and after one property change.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_property** | **str** | Property IRI. | 
**var_from** | **List[str]** | Values before the change. | 
**to** | **List[str]** | Values after the change. | 

## Example

```python
from coa_control_plane_server.models.ontology_domain_change import OntologyDomainChange

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyDomainChange from a JSON string
ontology_domain_change_instance = OntologyDomainChange.from_json(json)
# print the JSON string representation of the object
print(OntologyDomainChange.to_json())

# convert the object into a dict
ontology_domain_change_dict = ontology_domain_change_instance.to_dict()
# create an instance of OntologyDomainChange from a dict
ontology_domain_change_from_dict = OntologyDomainChange.from_dict(ontology_domain_change_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


