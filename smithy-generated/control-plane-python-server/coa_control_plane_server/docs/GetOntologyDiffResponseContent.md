# GetOntologyDiffResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**baseline_graph** | **str** | Baseline graph that was compared. | 
**target_graph** | **str** | Target graph that was compared. | 
**counts** | [**OntologyDiffCounts**](OntologyDiffCounts.md) |  | 
**added_classes** | **List[str]** | Class IRIs only in the target (sample). | 
**removed_classes** | **List[str]** | Class IRIs only in the baseline (sample). | 
**added_properties** | **List[str]** | Property IRIs only in the target (sample). | 
**removed_properties** | **List[str]** | Property IRIs only in the baseline (sample). | 
**examples** | [**OntologyDiffExamples**](OntologyDiffExamples.md) |  | 
**truncated** | **bool** | True when a sample list or example set was cut at &#x60;&#x60;limit&#x60;&#x60;. | 
**source** | **str** | Human-readable provenance for the diff. | 
**sampled_at** | **str** | When the diff ran (ISO-8601). | 

## Example

```python
from coa_control_plane_server.models.get_ontology_diff_response_content import GetOntologyDiffResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetOntologyDiffResponseContent from a JSON string
get_ontology_diff_response_content_instance = GetOntologyDiffResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetOntologyDiffResponseContent.to_json())

# convert the object into a dict
get_ontology_diff_response_content_dict = get_ontology_diff_response_content_instance.to_dict()
# create an instance of GetOntologyDiffResponseContent from a dict
get_ontology_diff_response_content_from_dict = GetOntologyDiffResponseContent.from_dict(get_ontology_diff_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


