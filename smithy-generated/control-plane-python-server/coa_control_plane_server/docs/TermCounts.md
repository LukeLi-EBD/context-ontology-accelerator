# TermCounts

Anchor-class and alias counts for the namespace's published T-Box.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**anchor_classes** | **float** | Distinct owl:Class nodes that an alias entry points at (F58). | 
**term_entries** | **float** | Number of skos:Concept / term:TermEntry alias entries (F59). | 
**evidenced** | **float** | Entries whose status is &#x60;evidenced&#x60;. | 
**inferred** | **float** | Entries whose status is &#x60;inferred&#x60;. | 

## Example

```python
from coa_control_plane_server.models.term_counts import TermCounts

# TODO update the JSON string below
json = "{}"
# create an instance of TermCounts from a JSON string
term_counts_instance = TermCounts.from_json(json)
# print the JSON string representation of the object
print(TermCounts.to_json())

# convert the object into a dict
term_counts_dict = term_counts_instance.to_dict()
# create an instance of TermCounts from a dict
term_counts_from_dict = TermCounts.from_dict(term_counts_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


