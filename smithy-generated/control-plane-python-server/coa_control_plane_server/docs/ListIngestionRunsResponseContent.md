# ListIngestionRunsResponseContent

Standard pagination output

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_token** | **str** | Opaque token for fetching the next page; absent when there are no more results. | [optional] 
**items** | [**List[IngestionRun]**](IngestionRun.md) | Page of ingestion runs. | 
**total_count** | **float** | Number of runs matching the filter across all pages. | 
**failures** | [**List[IngestionFailure]**](IngestionFailure.md) | Most recent failed items across the returned page (at most 20). | 

## Example

```python
from coa_control_plane_server.models.list_ingestion_runs_response_content import ListIngestionRunsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListIngestionRunsResponseContent from a JSON string
list_ingestion_runs_response_content_instance = ListIngestionRunsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListIngestionRunsResponseContent.to_json())

# convert the object into a dict
list_ingestion_runs_response_content_dict = list_ingestion_runs_response_content_instance.to_dict()
# create an instance of ListIngestionRunsResponseContent from a dict
list_ingestion_runs_response_content_from_dict = ListIngestionRunsResponseContent.from_dict(list_ingestion_runs_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


