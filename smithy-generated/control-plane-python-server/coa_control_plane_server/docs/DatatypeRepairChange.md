# DatatypeRepairChange

A single datatype-token rewrite applied by RepairProposalDatatypes.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**found** | **str** | The malformed datatype IRI that was found. | 
**canonical** | **str** | The canonical XSD datatype IRI it was rewritten to. | 

## Example

```python
from coa_control_plane_server.models.datatype_repair_change import DatatypeRepairChange

# TODO update the JSON string below
json = "{}"
# create an instance of DatatypeRepairChange from a JSON string
datatype_repair_change_instance = DatatypeRepairChange.from_json(json)
# print the JSON string representation of the object
print(DatatypeRepairChange.to_json())

# convert the object into a dict
datatype_repair_change_dict = datatype_repair_change_instance.to_dict()
# create an instance of DatatypeRepairChange from a dict
datatype_repair_change_from_dict = DatatypeRepairChange.from_dict(datatype_repair_change_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


