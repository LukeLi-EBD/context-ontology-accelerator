# ReviewSourceColumnRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**decision** | [**ReviewDecision**](ReviewDecision.md) |  | 

## Example

```python
from coa_control_plane_server.models.review_source_column_request_content import ReviewSourceColumnRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ReviewSourceColumnRequestContent from a JSON string
review_source_column_request_content_instance = ReviewSourceColumnRequestContent.from_json(json)
# print the JSON string representation of the object
print(ReviewSourceColumnRequestContent.to_json())

# convert the object into a dict
review_source_column_request_content_dict = review_source_column_request_content_instance.to_dict()
# create an instance of ReviewSourceColumnRequestContent from a dict
review_source_column_request_content_from_dict = ReviewSourceColumnRequestContent.from_dict(review_source_column_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


