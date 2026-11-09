# SourceSummary

Summary representation of a unified source (used in list responses). Contains only the fields common to all source types.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_id** | **str** | Unique source identifier. | 
**namespace_id** | **str** | UUID v4 identifier. | 
**name** | **str** | Display name of the source. | 
**source_type** | [**SourceType**](SourceType.md) |  | 
**source_sub_type** | [**SourceSubType**](SourceSubType.md) |  | 
**status** | [**SourceStatus**](SourceStatus.md) |  | 
**created_at** | **float** | Timestamp when the source was created. | 
**updated_at** | **float** | Timestamp when the source was last updated. | [optional] 
**tables_discovered** | **float** | Number of tables discovered in the most recent scan (DATABASE sources only). | [optional] 

## Example

```python
from coa_control_plane_server.models.source_summary import SourceSummary

# TODO update the JSON string below
json = "{}"
# create an instance of SourceSummary from a JSON string
source_summary_instance = SourceSummary.from_json(json)
# print the JSON string representation of the object
print(SourceSummary.to_json())

# convert the object into a dict
source_summary_dict = source_summary_instance.to_dict()
# create an instance of SourceSummary from a dict
source_summary_from_dict = SourceSummary.from_dict(source_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


