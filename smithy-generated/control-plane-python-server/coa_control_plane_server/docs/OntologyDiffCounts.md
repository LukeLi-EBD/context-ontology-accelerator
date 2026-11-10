# OntologyDiffCounts

Triple and schema delta counts.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**added_triples** | **float** | Triples present in the target and absent from the baseline. | 
**removed_triples** | **float** | Triples present in the baseline and absent from the target. | 
**added_classes** | **float** | Classes added. | 
**removed_classes** | **float** | Classes removed. | 
**added_properties** | **float** | Properties added (object or datatype). | 
**removed_properties** | **float** | Properties removed. | 

## Example

```python
from coa_control_plane_server.models.ontology_diff_counts import OntologyDiffCounts

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyDiffCounts from a JSON string
ontology_diff_counts_instance = OntologyDiffCounts.from_json(json)
# print the JSON string representation of the object
print(OntologyDiffCounts.to_json())

# convert the object into a dict
ontology_diff_counts_dict = ontology_diff_counts_instance.to_dict()
# create an instance of OntologyDiffCounts from a dict
ontology_diff_counts_from_dict = OntologyDiffCounts.from_dict(ontology_diff_counts_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


