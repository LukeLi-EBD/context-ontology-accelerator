# ListSourceScanJobsResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**items** | [**List[ScanJobEntry]**](ScanJobEntry.md) | History entries, newest first. | 

## Example

```python
from coa_control_plane_server.models.list_source_scan_jobs_response_content import ListSourceScanJobsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListSourceScanJobsResponseContent from a JSON string
list_source_scan_jobs_response_content_instance = ListSourceScanJobsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListSourceScanJobsResponseContent.to_json())

# convert the object into a dict
list_source_scan_jobs_response_content_dict = list_source_scan_jobs_response_content_instance.to_dict()
# create an instance of ListSourceScanJobsResponseContent from a dict
list_source_scan_jobs_response_content_from_dict = ListSourceScanJobsResponseContent.from_dict(list_source_scan_jobs_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


