# RetractFactsRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fact_ids** | **List[str]** | Explicit rows to retract (1-500); wins over the filters. | [optional] 
**subject** | **str** | Filter: only rows with this subject. | [optional] 
**predicate** | **str** | Filter: only rows with this predicate. | [optional] 
**graph** | **str** | Filter: only rows in this named graph. | [optional] 
**source_document_id** | **str** | Filter: only rows produced by this document. | [optional] 
**actor** | **str** | Identity recorded on every retract event; defaults to &#x60;operator&#x60;. | [optional] 
**reason** | **str** | Why the rows are withdrawn. | [optional] 
**dry_run** | **bool** | Preview only; defaults to true. | [optional] 

## Example

```python
from coa_control_plane_server.models.retract_facts_request_content import RetractFactsRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of RetractFactsRequestContent from a JSON string
retract_facts_request_content_instance = RetractFactsRequestContent.from_json(json)
# print the JSON string representation of the object
print(RetractFactsRequestContent.to_json())

# convert the object into a dict
retract_facts_request_content_dict = retract_facts_request_content_instance.to_dict()
# create an instance of RetractFactsRequestContent from a dict
retract_facts_request_content_from_dict = RetractFactsRequestContent.from_dict(retract_facts_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


