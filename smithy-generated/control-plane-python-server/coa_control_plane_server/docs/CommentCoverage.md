# CommentCoverage

Comment coverage rollup (F66). `ratio` is absent when there are no rows.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | **float** | Rows considered. | 
**commented** | **float** | Rows carrying a comment. | 
**missing** | **float** | Rows with no comment. | 
**ratio** | **float** | Commented rows divided by total, 0..1. | [optional] 

## Example

```python
from coa_control_plane_server.models.comment_coverage import CommentCoverage

# TODO update the JSON string below
json = "{}"
# create an instance of CommentCoverage from a JSON string
comment_coverage_instance = CommentCoverage.from_json(json)
# print the JSON string representation of the object
print(CommentCoverage.to_json())

# convert the object into a dict
comment_coverage_dict = comment_coverage_instance.to_dict()
# create an instance of CommentCoverage from a dict
comment_coverage_from_dict = CommentCoverage.from_dict(comment_coverage_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


