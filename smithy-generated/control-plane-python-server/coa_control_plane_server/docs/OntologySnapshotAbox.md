# OntologySnapshotAbox

Counts of asserted instances (the A-Box).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**instances** | **float** | Distinct subjects typed by a class declared in this namespace. | 
**classes_with_instances** | **float** | Distinct declared classes that carry at least one instance. | 

## Example

```python
from coa_control_plane_server.models.ontology_snapshot_abox import OntologySnapshotAbox

# TODO update the JSON string below
json = "{}"
# create an instance of OntologySnapshotAbox from a JSON string
ontology_snapshot_abox_instance = OntologySnapshotAbox.from_json(json)
# print the JSON string representation of the object
print(OntologySnapshotAbox.to_json())

# convert the object into a dict
ontology_snapshot_abox_dict = ontology_snapshot_abox_instance.to_dict()
# create an instance of OntologySnapshotAbox from a dict
ontology_snapshot_abox_from_dict = OntologySnapshotAbox.from_dict(ontology_snapshot_abox_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


