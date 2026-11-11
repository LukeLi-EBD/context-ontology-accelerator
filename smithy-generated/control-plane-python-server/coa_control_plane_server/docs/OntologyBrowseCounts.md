# OntologyBrowseCounts

Counts returned with the tree.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**classes** | **float** | Number of classes in the published T-Box. | 
**properties** | **float** | Number of properties in the published T-Box. | 

## Example

```python
from coa_control_plane_server.models.ontology_browse_counts import OntologyBrowseCounts

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyBrowseCounts from a JSON string
ontology_browse_counts_instance = OntologyBrowseCounts.from_json(json)
# print the JSON string representation of the object
print(OntologyBrowseCounts.to_json())

# convert the object into a dict
ontology_browse_counts_dict = ontology_browse_counts_instance.to_dict()
# create an instance of OntologyBrowseCounts from a dict
ontology_browse_counts_from_dict = OntologyBrowseCounts.from_dict(ontology_browse_counts_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


