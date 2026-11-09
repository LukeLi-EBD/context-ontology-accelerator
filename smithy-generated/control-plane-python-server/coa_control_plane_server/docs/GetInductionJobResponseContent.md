# GetInductionJobResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | UUID v4 identifier. | 
**status** | [**InductionJobStatus**](InductionJobStatus.md) |  | 
**created_at** | **float** | Timestamp when the induction job was created. | 
**report** | [**InductionReport**](InductionReport.md) |  | [optional] 
**source_type** | [**InductionSourceType**](InductionSourceType.md) |  | [optional] 
**progress** | **str** | Current step of a running bridge job, as short free text (e.g. \&quot;writing definitions for 12 tables\&quot;). | [optional] 
**bridge_report** | [**BridgeReport**](BridgeReport.md) |  | [optional] 
**error** | **str** | Error message (populated when status is FAILED). | [optional] 

## Example

```python
from coa_control_plane_server.models.get_induction_job_response_content import GetInductionJobResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetInductionJobResponseContent from a JSON string
get_induction_job_response_content_instance = GetInductionJobResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetInductionJobResponseContent.to_json())

# convert the object into a dict
get_induction_job_response_content_dict = get_induction_job_response_content_instance.to_dict()
# create an instance of GetInductionJobResponseContent from a dict
get_induction_job_response_content_from_dict = GetInductionJobResponseContent.from_dict(get_induction_job_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


