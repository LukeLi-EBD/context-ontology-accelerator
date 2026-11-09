# MetadataOverrides

Steward-supplied overrides applied to discovered metadata: description, synonyms, glossary terms, and tags.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**description** | **str** | Override description for the table or column. | [optional] 
**synonyms** | **List[str]** | Override synonyms or aliases. | [optional] 
**glossary_terms** | **List[str]** | Override business glossary terms. | [optional] 
**tags** | **List[str]** | Override classification tags. | [optional] 

## Example

```python
from coa_control_plane_server.models.metadata_overrides import MetadataOverrides

# TODO update the JSON string below
json = "{}"
# create an instance of MetadataOverrides from a JSON string
metadata_overrides_instance = MetadataOverrides.from_json(json)
# print the JSON string representation of the object
print(MetadataOverrides.to_json())

# convert the object into a dict
metadata_overrides_dict = metadata_overrides_instance.to_dict()
# create an instance of MetadataOverrides from a dict
metadata_overrides_from_dict = MetadataOverrides.from_dict(metadata_overrides_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


