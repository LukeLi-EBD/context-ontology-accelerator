# OntologyEventFilter

Filters accepted by `ListOntologyEvents`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version_id** | **str** | Version filter that was applied. | [optional] 
**action** | **str** | Action filter that was applied. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_event_filter import OntologyEventFilter

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyEventFilter from a JSON string
ontology_event_filter_instance = OntologyEventFilter.from_json(json)
# print the JSON string representation of the object
print(OntologyEventFilter.to_json())

# convert the object into a dict
ontology_event_filter_dict = ontology_event_filter_instance.to_dict()
# create an instance of OntologyEventFilter from a dict
ontology_event_filter_from_dict = OntologyEventFilter.from_dict(ontology_event_filter_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


