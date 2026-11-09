# ReviewSourceColumnResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**table_id** | **str** | Identifier of the table containing the column. | 
**column_name** | **str** | Name of the reviewed column. | 
**review_status** | [**ReviewStatus**](ReviewStatus.md) |  | 

## Example

```python
from coa_control_plane_server.models.review_source_column_response_content import ReviewSourceColumnResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ReviewSourceColumnResponseContent from a JSON string
review_source_column_response_content_instance = ReviewSourceColumnResponseContent.from_json(json)
# print the JSON string representation of the object
print(ReviewSourceColumnResponseContent.to_json())

# convert the object into a dict
review_source_column_response_content_dict = review_source_column_response_content_instance.to_dict()
# create an instance of ReviewSourceColumnResponseContent from a dict
review_source_column_response_content_from_dict = ReviewSourceColumnResponseContent.from_dict(review_source_column_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


