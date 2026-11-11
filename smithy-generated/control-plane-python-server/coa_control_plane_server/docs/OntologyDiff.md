# OntologyDiff

What changed between two versions.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_from** | **str** | Baseline version; absent when the target is the first version. | [optional] 
**to** | **str** | Target version. | 
**breaking** | **bool** | True when at least one breaking item exists. | 
**breaking_items** | [**List[OntologyBreakingItem]**](OntologyBreakingItem.md) | Elements that make the diff breaking. | 
**summary** | [**OntologyDiffSummary**](OntologyDiffSummary.md) |  | 
**markdown** | **str** | Pre-rendered Markdown description of the diff. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_diff import OntologyDiff

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyDiff from a JSON string
ontology_diff_instance = OntologyDiff.from_json(json)
# print the JSON string representation of the object
print(OntologyDiff.to_json())

# convert the object into a dict
ontology_diff_dict = ontology_diff_instance.to_dict()
# create an instance of OntologyDiff from a dict
ontology_diff_from_dict = OntologyDiff.from_dict(ontology_diff_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


