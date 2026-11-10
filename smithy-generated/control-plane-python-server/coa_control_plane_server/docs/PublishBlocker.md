# PublishBlocker

One reason a publish plan would refuse to publish.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**gate** | **str** | Gate that produced the blocker. | 
**code** | **str** | Provider error code. | 
**message** | **str** | Human-readable explanation. | 
**details** | **object** | Gate-specific detail. | [optional] 

## Example

```python
from coa_control_plane_server.models.publish_blocker import PublishBlocker

# TODO update the JSON string below
json = "{}"
# create an instance of PublishBlocker from a JSON string
publish_blocker_instance = PublishBlocker.from_json(json)
# print the JSON string representation of the object
print(PublishBlocker.to_json())

# convert the object into a dict
publish_blocker_dict = publish_blocker_instance.to_dict()
# create an instance of PublishBlocker from a dict
publish_blocker_from_dict = PublishBlocker.from_dict(publish_blocker_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


