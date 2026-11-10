# EntityProvenance

Fact-ledger provenance for the entity's subject.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**count** | **float** | Number of rows returned. | 
**items** | [**List[EntityProvenanceItem]**](EntityProvenanceItem.md) | Ledger rows. | 
**unavailable** | **bool** | True when the ledger could not be read. | [optional] 

## Example

```python
from coa_control_plane_server.models.entity_provenance import EntityProvenance

# TODO update the JSON string below
json = "{}"
# create an instance of EntityProvenance from a JSON string
entity_provenance_instance = EntityProvenance.from_json(json)
# print the JSON string representation of the object
print(EntityProvenance.to_json())

# convert the object into a dict
entity_provenance_dict = entity_provenance_instance.to_dict()
# create an instance of EntityProvenance from a dict
entity_provenance_from_dict = EntityProvenance.from_dict(entity_provenance_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


