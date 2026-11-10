# EntityBadge

Three-state evidence badge for the entity or one field.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | **str** | &#x60;evidenced&#x60;, &#x60;inferred&#x60;, or &#x60;none&#x60;. | 
**label** | **str** | Human-readable badge label. | 
**basis** | **str** | Why the badge has this state. | 
**judge** | **str** | Judge that produced the verdict, when one was used. | [optional] 

## Example

```python
from coa_control_plane_server.models.entity_badge import EntityBadge

# TODO update the JSON string below
json = "{}"
# create an instance of EntityBadge from a JSON string
entity_badge_instance = EntityBadge.from_json(json)
# print the JSON string representation of the object
print(EntityBadge.to_json())

# convert the object into a dict
entity_badge_dict = entity_badge_instance.to_dict()
# create an instance of EntityBadge from a dict
entity_badge_from_dict = EntityBadge.from_dict(entity_badge_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


