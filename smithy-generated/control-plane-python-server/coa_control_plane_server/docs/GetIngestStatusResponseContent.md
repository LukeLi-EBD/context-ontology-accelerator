# GetIngestStatusResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**result** | [**IngestJob**](IngestJob.md) |  | 

## Example

```python
from coa_control_plane_server.models.get_ingest_status_response_content import GetIngestStatusResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetIngestStatusResponseContent from a JSON string
get_ingest_status_response_content_instance = GetIngestStatusResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetIngestStatusResponseContent.to_json())

# convert the object into a dict
get_ingest_status_response_content_dict = get_ingest_status_response_content_instance.to_dict()
# create an instance of GetIngestStatusResponseContent from a dict
get_ingest_status_response_content_from_dict = GetIngestStatusResponseContent.from_dict(get_ingest_status_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


