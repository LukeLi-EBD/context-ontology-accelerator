# AssertFactRequestContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**subject** | **str** | Subject IRI. | 
**predicate** | **str** | Predicate IRI. | 
**object** | **str** | Object value; an IRI when &#x60;objectKind&#x60; is &#x60;iri&#x60;. | 
**object_kind** | [**FactObjectKind**](FactObjectKind.md) |  | 
**graph** | **str** | Named graph the assertion belongs to. | [optional] 
**source_kind** | [**FactSourceKind**](FactSourceKind.md) |  | [optional] 
**source_document_id** | **str** | Document that produced the row, when any. | [optional] 
**source_run_id** | **str** | Ingestion run that produced the row, when any. | [optional] 
**actor** | **str** | Identity recorded on the assert event. | [optional] 

## Example

```python
from coa_control_plane_server.models.assert_fact_request_content import AssertFactRequestContent

# TODO update the JSON string below
json = "{}"
# create an instance of AssertFactRequestContent from a JSON string
assert_fact_request_content_instance = AssertFactRequestContent.from_json(json)
# print the JSON string representation of the object
print(AssertFactRequestContent.to_json())

# convert the object into a dict
assert_fact_request_content_dict = assert_fact_request_content_instance.to_dict()
# create an instance of AssertFactRequestContent from a dict
assert_fact_request_content_from_dict = AssertFactRequestContent.from_dict(assert_fact_request_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


