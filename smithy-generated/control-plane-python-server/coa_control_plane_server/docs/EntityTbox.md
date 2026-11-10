# EntityTbox

T-Box snapshot the read was evaluated against.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version_id** | **str** | Published version identifier. | [optional] 
**semver** | **str** | Published semantic version. | [optional] 
**graph** | **str** | Named graph that holds the T-Box. | [optional] 

## Example

```python
from coa_control_plane_server.models.entity_tbox import EntityTbox

# TODO update the JSON string below
json = "{}"
# create an instance of EntityTbox from a JSON string
entity_tbox_instance = EntityTbox.from_json(json)
# print the JSON string representation of the object
print(EntityTbox.to_json())

# convert the object into a dict
entity_tbox_dict = entity_tbox_instance.to_dict()
# create an instance of EntityTbox from a dict
entity_tbox_from_dict = EntityTbox.from_dict(entity_tbox_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


