# GetOntologySnapshotResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tbox** | [**OntologySnapshotTbox**](OntologySnapshotTbox.md) |  | 
**abox** | [**OntologySnapshotAbox**](OntologySnapshotAbox.md) |  | 
**coverage** | [**OntologyCoverage**](OntologyCoverage.md) |  | 
**graphs** | **List[str]** | Named graphs in this namespace, so the diff form can offer real choices. | 
**source** | **str** | Human-readable provenance for the numbers above. | 
**sampled_at** | **str** | When the aggregation ran (ISO-8601). | 

## Example

```python
from coa_control_plane_server.models.get_ontology_snapshot_response_content import GetOntologySnapshotResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOntologySnapshotResponseContent from a JSON string
get_ontology_snapshot_response_content_instance = GetOntologySnapshotResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetOntologySnapshotResponseContent.to_json())

# convert the object into a dict
get_ontology_snapshot_response_content_dict = get_ontology_snapshot_response_content_instance.to_dict()
# create an instance of GetOntologySnapshotResponseContent from a dict
get_ontology_snapshot_response_content_from_dict = GetOntologySnapshotResponseContent.from_dict(get_ontology_snapshot_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


