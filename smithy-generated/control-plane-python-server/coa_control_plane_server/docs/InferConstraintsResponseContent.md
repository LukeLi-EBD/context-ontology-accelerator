# InferConstraintsResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | UUID v4 identifier. | 
**proposal_id** | **str** | UUID v4 identifier. | 
**status** | **str** | Initial job status (pending). | 

## Example

```python
from coa_control_plane_server.models.infer_constraints_response_content import InferConstraintsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of InferConstraintsResponseContent from a JSON string
infer_constraints_response_content_instance = InferConstraintsResponseContent.from_json(json)
# print the JSON string representation of the object
print(InferConstraintsResponseContent.to_json())

# convert the object into a dict
infer_constraints_response_content_dict = infer_constraints_response_content_instance.to_dict()
# create an instance of InferConstraintsResponseContent from a dict
infer_constraints_response_content_from_dict = InferConstraintsResponseContent.from_dict(infer_constraints_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


