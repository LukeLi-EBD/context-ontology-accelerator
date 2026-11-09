# ExportOsiResponseContent

Result of an OSI export, either inline YAML content or a pre-signed download URL.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**content** | **str** | OSI YAML content (populated when format&#x3D;inline or omitted). | [optional] 
**download_url** | **str** | Pre-signed S3 GET URL for downloading the export (populated when format&#x3D;s3). | [optional] 
**expires_in** | **float** | Seconds until the download URL expires (populated when format&#x3D;s3). | [optional] 

## Example

```python
from coa_control_plane_server.models.export_osi_response_content import ExportOsiResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ExportOsiResponseContent from a JSON string
export_osi_response_content_instance = ExportOsiResponseContent.from_json(json)
# print the JSON string representation of the object
print(ExportOsiResponseContent.to_json())

# convert the object into a dict
export_osi_response_content_dict = export_osi_response_content_instance.to_dict()
# create an instance of ExportOsiResponseContent from a dict
export_osi_response_content_from_dict = ExportOsiResponseContent.from_dict(export_osi_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


