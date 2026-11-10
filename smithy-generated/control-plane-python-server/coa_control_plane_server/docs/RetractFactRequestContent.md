# RetractFactRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**actor** | **str** | Identity recorded on the retract event; defaults to &#x60;api&#x60;. | [optional] 
**reason** | **str** | Why the row is withdrawn. | [optional] 

## Example

```python
from coa_control_plane_server.models.retract_fact_request_content import RetractFactRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RetractFactRequestContent from a JSON string
retract_fact_request_content_instance = RetractFactRequestContent.from_json(json)
# print the JSON string representation of the object
print(RetractFactRequestContent.to_json())

# convert the object into a dict
retract_fact_request_content_dict = retract_fact_request_content_instance.to_dict()
# create an instance of RetractFactRequestContent from a dict
retract_fact_request_content_from_dict = RetractFactRequestContent.from_dict(retract_fact_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


