# BatchKeepFactConflictsRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**keep** | **str** | Value to keep in every matched group; required. | 
**predicate** | **str** | Only groups with this predicate. | [optional] 
**subject** | **str** | Only groups with this subject. | [optional] 
**source_document_id** | **str** | Only groups that contain a row from this document. | [optional] 
**actor** | **str** | Identity recorded on every adjudication event; defaults to &#x60;operator&#x60;. | [optional] 
**reason** | **str** | Why the rule is applied. | [optional] 
**dry_run** | **bool** | Preview only; defaults to true. | [optional] 

## Example

```python
from coa_control_plane_server.models.batch_keep_fact_conflicts_request_content import BatchKeepFactConflictsRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of BatchKeepFactConflictsRequestContent from a JSON string
batch_keep_fact_conflicts_request_content_instance = BatchKeepFactConflictsRequestContent.from_json(json)
# print the JSON string representation of the object
print(BatchKeepFactConflictsRequestContent.to_json())

# convert the object into a dict
batch_keep_fact_conflicts_request_content_dict = batch_keep_fact_conflicts_request_content_instance.to_dict()
# create an instance of BatchKeepFactConflictsRequestContent from a dict
batch_keep_fact_conflicts_request_content_from_dict = BatchKeepFactConflictsRequestContent.from_dict(batch_keep_fact_conflicts_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


