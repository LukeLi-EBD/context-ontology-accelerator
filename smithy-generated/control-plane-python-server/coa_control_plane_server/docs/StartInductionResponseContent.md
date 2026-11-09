# StartInductionResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | Unique job identifier for tracking progress. | 

## Example

```python
from coa_control_plane_server.models.start_induction_response_content import StartInductionResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of StartInductionResponseContent from a JSON string
start_induction_response_content_instance = StartInductionResponseContent.from_json(json)
# print the JSON string representation of the object
print(StartInductionResponseContent.to_json())

# convert the object into a dict
start_induction_response_content_dict = start_induction_response_content_instance.to_dict()
# create an instance of StartInductionResponseContent from a dict
start_induction_response_content_from_dict = StartInductionResponseContent.from_dict(start_induction_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


