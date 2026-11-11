# IngestionRunItem

One discovered file inside an import batch (platform.import_item).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**rel_path** | **str** | Path relative to the batch root. | 
**status** | **str** | Item lifecycle state exactly as stored by the importer (pending / parsing / chunked / indexed / failed). | 
**attempts** | **float** | Number of processing attempts so far. | 
**failure_code** | **str** | Machine-readable failure code; absent unless the item failed. | [optional] 
**failure_message** | **str** | Human-readable failure message; absent unless the item failed. | [optional] 
**updated_at** | **datetime** | When the item last changed. | 

## Example

```python
from coa_control_plane_server.models.ingestion_run_item import IngestionRunItem

# TODO update the JSON string below
json = "{}"
# create an instance of IngestionRunItem from a JSON string
ingestion_run_item_instance = IngestionRunItem.from_json(json)
# print the JSON string representation of the object
print(IngestionRunItem.to_json())

# convert the object into a dict
ingestion_run_item_dict = ingestion_run_item_instance.to_dict()
# create an instance of IngestionRunItem from a dict
ingestion_run_item_from_dict = IngestionRunItem.from_dict(ingestion_run_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


