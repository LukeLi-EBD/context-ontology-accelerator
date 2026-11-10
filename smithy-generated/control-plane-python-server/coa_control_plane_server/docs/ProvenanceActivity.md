# ProvenanceActivity

One PROV activity related to the entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**activity_id** | **str** | Activity IRI. | 
**relation** | **str** | Relation between the entity and the activity. | 
**object** | **str** | Object of the relation, when any. | [optional] 
**graph** | **str** | Named graph that holds the relation. | [optional] 

## Example

```python
from coa_control_plane_server.models.provenance_activity import ProvenanceActivity

# TODO update the JSON string below
json = "{}"
# create an instance of ProvenanceActivity from a JSON string
provenance_activity_instance = ProvenanceActivity.from_json(json)
# print the JSON string representation of the object
print(ProvenanceActivity.to_json())

# convert the object into a dict
provenance_activity_dict = provenance_activity_instance.to_dict()
# create an instance of ProvenanceActivity from a dict
provenance_activity_from_dict = ProvenanceActivity.from_dict(provenance_activity_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


