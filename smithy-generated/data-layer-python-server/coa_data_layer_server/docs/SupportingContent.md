# SupportingContent

A knowledge-base chunk that supports an answer, with its text, source document provenance, and relevance score.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**chunk_id** | **str** | Identifier of the knowledge-base chunk. | 
**text** | **str** | Text content of the chunk. | 
**source_document_id** | **str** | Opaque, unique identifier of the source document the chunk came from. Use this value to correlate chunks; it is not a display name. | [optional] 
**source_document_name** | **str** | Human-readable original file name of the source document. This value is intended for display and is not guaranteed to be unique. | [optional] 
**relevance_score** | **float** | Relevance score of the chunk to the query. | [optional] 
**entity_annotations** | **List[str]** | Entities annotated within the chunk. | [optional] 

## Example

```python
from coa_data_layer_server.models.supporting_content import SupportingContent

# TODO update the JSON string below
json = "{}"
# create an instance of SupportingContent from a JSON string
supporting_content_instance = SupportingContent.from_json(json)
# print the JSON string representation of the object
print(SupportingContent.to_json())

# convert the object into a dict
supporting_content_dict = supporting_content_instance.to_dict()
# create an instance of SupportingContent from a dict
supporting_content_from_dict = SupportingContent.from_dict(supporting_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


