# TermEntry

One alias row. The seven data columns are class, label, status, confidence, guard regex, canonical-for targets and suppressed surfaces.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**entry** | **str** | IRI of the skos:Concept / term:TermEntry node. | 
**class_iri** | **str** | IRI of the anchored class. | [optional] 
**class_label** | **str** | rdfs:label of the anchored class, when the graph carries one. | [optional] 
**label** | **str** | The alias surface form (skos:prefLabel or term:label). | 
**status** | **str** | &#x60;evidenced&#x60; or &#x60;inferred&#x60;. | 
**confidence** | **float** | Term confidence, 0..1, when recorded. | [optional] 
**guard_regex** | **str** | Guard regular expression that must pass before the alias is used. | [optional] 
**canonical_for** | **List[str]** | Concepts this surface is the canonical label for. | [optional] 
**suppressed_surface** | **List[str]** | Surface forms suppressed in favour of this entry. | [optional] 

## Example

```python
from coa_control_plane_server.models.term_entry import TermEntry

# TODO update the JSON string below
json = "{}"
# create an instance of TermEntry from a JSON string
term_entry_instance = TermEntry.from_json(json)
# print the JSON string representation of the object
print(TermEntry.to_json())

# convert the object into a dict
term_entry_dict = term_entry_instance.to_dict()
# create an instance of TermEntry from a dict
term_entry_from_dict = TermEntry.from_dict(term_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


