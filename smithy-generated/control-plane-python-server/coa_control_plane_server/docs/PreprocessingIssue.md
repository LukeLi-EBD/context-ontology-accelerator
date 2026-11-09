# PreprocessingIssue

A single file-level preprocessing issue recorded during ingestion.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**filename** | **str** | Name of the file the issue applies to. | 
**type** | [**PreprocessingIssueType**](PreprocessingIssueType.md) |  | 
**reason** | **str** | Human-readable explanation of the issue. | 

## Example

```python
from coa_control_plane_server.models.preprocessing_issue import PreprocessingIssue

# TODO update the JSON string below
json = "{}"
# create an instance of PreprocessingIssue from a JSON string
preprocessing_issue_instance = PreprocessingIssue.from_json(json)
# print the JSON string representation of the object
print(PreprocessingIssue.to_json())

# convert the object into a dict
preprocessing_issue_dict = preprocessing_issue_instance.to_dict()
# create an instance of PreprocessingIssue from a dict
preprocessing_issue_from_dict = PreprocessingIssue.from_dict(preprocessing_issue_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


