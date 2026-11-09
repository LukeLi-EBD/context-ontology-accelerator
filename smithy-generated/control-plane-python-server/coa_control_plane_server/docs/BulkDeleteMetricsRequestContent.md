# BulkDeleteMetricsRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**names** | **List[str]** | Explicit list of metric names to delete. Mutually exclusive with filter. | [optional] 
**filter** | [**BulkDeleteFilter**](BulkDeleteFilter.md) |  | [optional] 
**delete_all** | **bool** | Delete every metric in the namespace (used by namespace deletion). Mutually exclusive with names and filter. | [optional] 

## Example

```python
from coa_control_plane_server.models.bulk_delete_metrics_request_content import BulkDeleteMetricsRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of BulkDeleteMetricsRequestContent from a JSON string
bulk_delete_metrics_request_content_instance = BulkDeleteMetricsRequestContent.from_json(json)
# print the JSON string representation of the object
print(BulkDeleteMetricsRequestContent.to_json())

# convert the object into a dict
bulk_delete_metrics_request_content_dict = bulk_delete_metrics_request_content_instance.to_dict()
# create an instance of BulkDeleteMetricsRequestContent from a dict
bulk_delete_metrics_request_content_from_dict = BulkDeleteMetricsRequestContent.from_dict(bulk_delete_metrics_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


