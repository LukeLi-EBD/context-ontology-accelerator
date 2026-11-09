# InductionJobSummary

Summary of an induction job (for list views).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | UUID v4 identifier. | 
**status** | [**InductionJobStatus**](InductionJobStatus.md) |  | 
**created_at** | **float** | Timestamp when the induction job was created. | 
**source_type** | [**InductionSourceType**](InductionSourceType.md) |  | [optional] 
**tables_processed** | **float** | Number of tables processed (populated after completion). | [optional] 
**novel_classes_created** | **float** | Number of novel classes created. | [optional] 
**error** | **str** | Error message if failed. | [optional] 

## Example

```python
from coa_control_plane_server.models.induction_job_summary import InductionJobSummary

# TODO update the JSON string below
json = "{}"
# create an instance of InductionJobSummary from a JSON string
induction_job_summary_instance = InductionJobSummary.from_json(json)
# print the JSON string representation of the object
print(InductionJobSummary.to_json())

# convert the object into a dict
induction_job_summary_dict = induction_job_summary_instance.to_dict()
# create an instance of InductionJobSummary from a dict
induction_job_summary_from_dict = InductionJobSummary.from_dict(induction_job_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


