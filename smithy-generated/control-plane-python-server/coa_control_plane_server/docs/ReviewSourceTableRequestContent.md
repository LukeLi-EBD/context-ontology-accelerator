# ReviewSourceTableRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**decision** | [**ReviewDecision**](ReviewDecision.md) |  | 

## Example

```python
from coa_control_plane_server.models.review_source_table_request_content import ReviewSourceTableRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of ReviewSourceTableRequestContent from a JSON string
review_source_table_request_content_instance = ReviewSourceTableRequestContent.from_json(json)
# print the JSON string representation of the object
print(ReviewSourceTableRequestContent.to_json())

# convert the object into a dict
review_source_table_request_content_dict = review_source_table_request_content_instance.to_dict()
# create an instance of ReviewSourceTableRequestContent from a dict
review_source_table_request_content_from_dict = ReviewSourceTableRequestContent.from_dict(review_source_table_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


