# ValidateMetricResponseContent

Result of validating a metric definition, listing blocking and advisory findings.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**warnings** | [**List[ValidationWarning]**](ValidationWarning.md) | Validation findings. Severity ERROR predicts create/update rejection; INFO is advisory. | 

## Example

```python
from coa_control_plane_server.models.validate_metric_response_content import ValidateMetricResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ValidateMetricResponseContent from a JSON string
validate_metric_response_content_instance = ValidateMetricResponseContent.from_json(json)
# print the JSON string representation of the object
print(ValidateMetricResponseContent.to_json())

# convert the object into a dict
validate_metric_response_content_dict = validate_metric_response_content_instance.to_dict()
# create an instance of ValidateMetricResponseContent from a dict
validate_metric_response_content_from_dict = ValidateMetricResponseContent.from_dict(validate_metric_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


