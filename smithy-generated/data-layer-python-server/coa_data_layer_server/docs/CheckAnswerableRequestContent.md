# CheckAnswerableRequestContent

Input for CheckAnswerable.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** | The natural-language question to pre-check. | 
**ontology_version** | **str** | Ontology version to check against; defaults to the published current one. | [optional] 
**min_coverage** | **float** | Minimum term coverage (0..1) required for &#x60;answerable: true&#x60;. | [optional] 

## Example

```python
from coa_data_layer_server.models.check_answerable_request_content import CheckAnswerableRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of CheckAnswerableRequestContent from a JSON string
check_answerable_request_content_instance = CheckAnswerableRequestContent.from_json(json)
# print the JSON string representation of the object
print(CheckAnswerableRequestContent.to_json())

# convert the object into a dict
check_answerable_request_content_dict = check_answerable_request_content_instance.to_dict()
# create an instance of CheckAnswerableRequestContent from a dict
check_answerable_request_content_from_dict = CheckAnswerableRequestContent.from_dict(check_answerable_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


