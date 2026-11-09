# GetImportJobResponseContent

Current status and progress counters for an asynchronous OSI import job.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | Identifier of the import job. | 
**status** | [**ImportJobStatus**](ImportJobStatus.md) |  | 
**metrics_total** | **float** | Total number of metrics in the import. | 
**metrics_processed** | **float** | Number of metrics processed so far. | 
**metrics_created** | **float** | Number of new metrics created so far. | 
**metrics_updated** | **float** | Number of existing metrics updated so far. | 
**errors** | **List[str]** | Fatal errors encountered during the import. | [optional] 
**warnings** | **List[str]** | Non-fatal warnings raised during the import. | [optional] 

## Example

```python
from coa_control_plane_server.models.get_import_job_response_content import GetImportJobResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetImportJobResponseContent from a JSON string
get_import_job_response_content_instance = GetImportJobResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetImportJobResponseContent.to_json())

# convert the object into a dict
get_import_job_response_content_dict = get_import_job_response_content_instance.to_dict()
# create an instance of GetImportJobResponseContent from a dict
get_import_job_response_content_from_dict = GetImportJobResponseContent.from_dict(get_import_job_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


