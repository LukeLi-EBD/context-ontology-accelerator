# GetDictionaryCommentCoverageResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Source the coverage applies to. | 
**coverage** | [**CommentCoverage**](CommentCoverage.md) |  | 
**tables** | [**List[DictionaryTableSummary]**](DictionaryTableSummary.md) | Per-table coverage rollups. | 

## Example

```python
from coa_control_plane_server.models.get_dictionary_comment_coverage_response_content import GetDictionaryCommentCoverageResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetDictionaryCommentCoverageResponseContent from a JSON string
get_dictionary_comment_coverage_response_content_instance = GetDictionaryCommentCoverageResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetDictionaryCommentCoverageResponseContent.to_json())

# convert the object into a dict
get_dictionary_comment_coverage_response_content_dict = get_dictionary_comment_coverage_response_content_instance.to_dict()
# create an instance of GetDictionaryCommentCoverageResponseContent from a dict
get_dictionary_comment_coverage_response_content_from_dict = GetDictionaryCommentCoverageResponseContent.from_dict(get_dictionary_comment_coverage_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


