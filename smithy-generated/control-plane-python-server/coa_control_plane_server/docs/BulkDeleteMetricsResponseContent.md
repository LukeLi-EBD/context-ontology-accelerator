# BulkDeleteMetricsResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**deleted** | **float** | Number of metrics deleted. | 
**not_found** | **List[str]** | Metric names that were not found (from names list). | [optional] 

## Example

```python
from coa_control_plane_server.models.bulk_delete_metrics_response_content import BulkDeleteMetricsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of BulkDeleteMetricsResponseContent from a JSON string
bulk_delete_metrics_response_content_instance = BulkDeleteMetricsResponseContent.from_json(json)
# print the JSON string representation of the object
print(BulkDeleteMetricsResponseContent.to_json())

# convert the object into a dict
bulk_delete_metrics_response_content_dict = bulk_delete_metrics_response_content_instance.to_dict()
# create an instance of BulkDeleteMetricsResponseContent from a dict
bulk_delete_metrics_response_content_from_dict = BulkDeleteMetricsResponseContent.from_dict(bulk_delete_metrics_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


