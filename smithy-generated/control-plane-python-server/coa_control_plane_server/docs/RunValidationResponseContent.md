# RunValidationResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**orphan_instances** | [**QualityCount**](QualityCount.md) |  | 
**unlabeled_classes** | [**QualityCount**](QualityCount.md) |  | 
**shacl** | [**ShaclReport**](ShaclReport.md) |  | 
**inference_failures** | [**QualityCount**](QualityCount.md) |  | 
**source** | **str** | Human-readable provenance for the checks above. | 
**sampled_at** | **str** | When the checks ran (ISO-8601). | 

## Example

```python
from coa_control_plane_server.models.run_validation_response_content import RunValidationResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of RunValidationResponseContent from a JSON string
run_validation_response_content_instance = RunValidationResponseContent.from_json(json)
# print the JSON string representation of the object
print(RunValidationResponseContent.to_json())

# convert the object into a dict
run_validation_response_content_dict = run_validation_response_content_instance.to_dict()
# create an instance of RunValidationResponseContent from a dict
run_validation_response_content_from_dict = RunValidationResponseContent.from_dict(run_validation_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


