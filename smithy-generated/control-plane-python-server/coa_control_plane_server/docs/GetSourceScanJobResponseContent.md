# GetSourceScanJobResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | Unique scan job identifier. | 
**source_id** | **str** | Identifier of the source scanned. | 
**status** | [**SourceScanJobStatus**](SourceScanJobStatus.md) |  | 
**tables_discovered** | **float** | Number of tables discovered by the scan. | [optional] 
**tables_processed** | **float** | Tables processed so far, counting both unchanged-on-inspection and enriched. Published as the job advances, so it lags by a few seconds. | [optional] 
**tables_total** | **float** | Denominator for &#x60;tablesProcessed&#x60;. Falls back to the previous scan&#39;s table count until this scan&#39;s discovery has finished enumerating. | [optional] 
**tables_added** | **float** | Number of tables added since the previous scan. | [optional] 
**tables_removed** | **float** | Number of tables removed since the previous scan. | [optional] 
**tables_modified** | **float** | Number of tables modified since the previous scan. | [optional] 
**started_at** | **float** | Timestamp when the scan job started. | 
**completed_at** | **float** | Timestamp when the scan job completed. | [optional] 
**error_message** | **str** | Error message if the scan job failed. | [optional] 
**tables_failed** | **float** | Number of tables the scan listed but could not read.  Absent when none failed, rather than zero, so it can be used directly to filter for degraded scans. A non-zero value means the scan SUCCEEDED but is incomplete: those tables carry no columns, no comments, and no declared keys, and AI enrichment will have generated descriptions over the gap — so a reviewer must not read the result as complete. Only connectors that read each table separately can report this; one that returns a table&#39;s schema in the same call that lists it cannot partially fail. | [optional] 
**failed_tables** | **List[str]** | The unreadable tables as &#x60;database.table&#x60;, capped in length.  A signal for diagnosis, not an inventory — &#x60;tablesFailed&#x60; is the exact figure and this list may be shorter than it. | [optional] 
**filter_warnings** | **List[str]** | Warnings about the source&#39;s filters, absent when none. Set when a filter that looks like a regular expression matched nothing — filters are globs, so the scan succeeded without the intended filtering. | [optional] 

## Example

```python
from coa_control_plane_server.models.get_source_scan_job_response_content import GetSourceScanJobResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetSourceScanJobResponseContent from a JSON string
get_source_scan_job_response_content_instance = GetSourceScanJobResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetSourceScanJobResponseContent.to_json())

# convert the object into a dict
get_source_scan_job_response_content_dict = get_source_scan_job_response_content_instance.to_dict()
# create an instance of GetSourceScanJobResponseContent from a dict
get_source_scan_job_response_content_from_dict = GetSourceScanJobResponseContent.from_dict(get_source_scan_job_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


