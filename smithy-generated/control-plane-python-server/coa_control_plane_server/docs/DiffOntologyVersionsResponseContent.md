# DiffOntologyVersionsResponseContent

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
from coa_control_plane_server.models.diff_ontology_versions_response_content import DiffOntologyVersionsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of DiffOntologyVersionsResponseContent from a JSON string
diff_ontology_versions_response_content_instance = DiffOntologyVersionsResponseContent.from_json(json)
# print the JSON string representation of the object
print(DiffOntologyVersionsResponseContent.to_json())

# convert the object into a dict
diff_ontology_versions_response_content_dict = diff_ontology_versions_response_content_instance.to_dict()
# create an instance of DiffOntologyVersionsResponseContent from a dict
diff_ontology_versions_response_content_from_dict = DiffOntologyVersionsResponseContent.from_dict(diff_ontology_versions_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


