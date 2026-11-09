# ImportOsiResponseContent

Result of an OSI import, summarizing resolved datasets and metric changes.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**datasets_resolved** | **float** | Number of datasets resolved from the OSI document. | 
**metrics_created** | **float** | Number of new metrics created by the import. | 
**metrics_updated** | **float** | Number of existing metrics updated by the import. | 
**warnings** | **List[str]** | Non-fatal warnings raised during the import. | [optional] 
**job_id** | **str** | Present when the import is processed asynchronously (metric count &gt; threshold). Poll GetImportJob with this ID to track progress. | [optional] 
**status** | [**ImportJobStatus**](ImportJobStatus.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.import_osi_response_content import ImportOsiResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ImportOsiResponseContent from a JSON string
import_osi_response_content_instance = ImportOsiResponseContent.from_json(json)
# print the JSON string representation of the object
print(ImportOsiResponseContent.to_json())

# convert the object into a dict
import_osi_response_content_dict = import_osi_response_content_instance.to_dict()
# create an instance of ImportOsiResponseContent from a dict
import_osi_response_content_from_dict = ImportOsiResponseContent.from_dict(import_osi_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


