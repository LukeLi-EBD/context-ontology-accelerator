# IngestionRunSkipped

Scan buckets that never became import items.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**hidden** | **float** | Dotfiles and other paths ignored by the scanner. | 
**unsupported** | **float** | Files whose extension is outside ALLOWED_EXTENSIONS. | 
**empty** | **float** | Zero-byte files. | 
**too_large** | **float** | Files above documents.max_upload_bytes. | 
**unreadable** | **float** | Files that could not be stat&#39;ed or hashed. | 

## Example

```python
from coa_control_plane_server.models.ingestion_run_skipped import IngestionRunSkipped

# TODO update the JSON string below
json = "{}"
# create an instance of IngestionRunSkipped from a JSON string
ingestion_run_skipped_instance = IngestionRunSkipped.from_json(json)
# print the JSON string representation of the object
print(IngestionRunSkipped.to_json())

# convert the object into a dict
ingestion_run_skipped_dict = ingestion_run_skipped_instance.to_dict()
# create an instance of IngestionRunSkipped from a dict
ingestion_run_skipped_from_dict = IngestionRunSkipped.from_dict(ingestion_run_skipped_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


