# ListAnswerQualityRunsResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[AnswerQualityRun]**](AnswerQualityRun.md) | Stored runs, newest first. | 
**total_count** | **float** | Number of runs matching the filter, across all pages. | 
**limit** | **float** | Page size used for this response. | 
**strategy** | [**AnswerQualityStrategy**](AnswerQualityStrategy.md) |  | [optional] 
**since** | **datetime** | Time-window lower bound echoed back; absent when unfiltered. | [optional] 
**read_only** | **bool** | Always true: this operation never writes. | 

## Example

```python
from coa_control_plane_server.models.list_answer_quality_runs_response_content import ListAnswerQualityRunsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListAnswerQualityRunsResponseContent from a JSON string
list_answer_quality_runs_response_content_instance = ListAnswerQualityRunsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListAnswerQualityRunsResponseContent.to_json())

# convert the object into a dict
list_answer_quality_runs_response_content_dict = list_answer_quality_runs_response_content_instance.to_dict()
# create an instance of ListAnswerQualityRunsResponseContent from a dict
list_answer_quality_runs_response_content_from_dict = ListAnswerQualityRunsResponseContent.from_dict(list_answer_quality_runs_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


