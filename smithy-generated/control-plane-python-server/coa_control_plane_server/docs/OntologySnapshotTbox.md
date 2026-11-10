# OntologySnapshotTbox

Counts of declared schema objects (the T-Box).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**classes** | **float** | Distinct &#x60;&#x60;owl:Class&#x60;&#x60; IRIs. | 
**object_properties** | **float** | Distinct &#x60;&#x60;owl:ObjectProperty&#x60;&#x60; IRIs. | 
**datatype_properties** | **float** | Distinct &#x60;&#x60;owl:DatatypeProperty&#x60;&#x60; IRIs. | 

## Example

```python
from coa_control_plane_server.models.ontology_snapshot_tbox import OntologySnapshotTbox

# TODO update the JSON string below
json = "{}"
# create an instance of OntologySnapshotTbox from a JSON string
ontology_snapshot_tbox_instance = OntologySnapshotTbox.from_json(json)
# print the JSON string representation of the object
print(OntologySnapshotTbox.to_json())

# convert the object into a dict
ontology_snapshot_tbox_dict = ontology_snapshot_tbox_instance.to_dict()
# create an instance of OntologySnapshotTbox from a dict
ontology_snapshot_tbox_from_dict = OntologySnapshotTbox.from_dict(ontology_snapshot_tbox_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


