# ScanJobEntry

One row in a source's scan history.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**at** | **float** | When the entry occurred (scan start, or the moment the review resolved). | 
**event_type** | [**ScanJobEventType**](ScanJobEventType.md) |  | [optional] 
**status** | **str** | Status of the row. For a SCAN this is the scan-job status (IN_PROGRESS/DISCOVERING/ENRICHING/COMPLETED/FAILED/CANCELLED); for a REVIEW it is the terminal source status the decision produced (e.g. APPROVED, REJECTED, APPROVAL_FAILED). Free-form because the two event kinds draw from different status vocabularies. | [optional] 
**scan_type** | **str** | For a SCAN row: whether it was a full or incremental (re-scan) run. | [optional] 
**trigger_type** | [**ScanTrigger**](ScanTrigger.md) |  | [optional] 
**tables_discovered** | **float** | Number of tables discovered by the scan (SCAN rows). | [optional] 
**tables_approved** | **float** | Number of tables approved as of this review (REVIEW rows). | [optional] 
**completed_at** | **float** | Timestamp when the scan job completed (SCAN rows). | [optional] 
**error_message** | **str** | Error message if the scan job failed (SCAN rows). | [optional] 
**decision** | [**ReviewDecision**](ReviewDecision.md) |  | [optional] 
**is_rescan** | **bool** | True when this event resolved a re-scan review (rather than an initial approve/reject). REVIEW rows only. | [optional] 

## Example

```python
from coa_control_plane_server.models.scan_job_entry import ScanJobEntry

# TODO update the JSON string below
json = "{}"
# create an instance of ScanJobEntry from a JSON string
scan_job_entry_instance = ScanJobEntry.from_json(json)
# print the JSON string representation of the object
print(ScanJobEntry.to_json())

# convert the object into a dict
scan_job_entry_dict = scan_job_entry_instance.to_dict()
# create an instance of ScanJobEntry from a dict
scan_job_entry_from_dict = ScanJobEntry.from_dict(scan_job_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


