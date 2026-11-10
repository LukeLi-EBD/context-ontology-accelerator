# StartOntologyValidationResponseContent

One asynchronous validation job, as returned by start and by poll.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | Server-assigned job identifier. | 
**status** | [**OntologyValidationJobStatus**](OntologyValidationJobStatus.md) |  | 
**created_at** | **str** | When the job was accepted (ISO-8601). | 
**report** | [**OntologyValidationReport**](OntologyValidationReport.md) |  | [optional] 
**error** | **str** | Failure reason, present only when &#x60;status&#x60; is &#x60;failed&#x60;. | [optional] 

## Example

```python
from coa_control_plane_server.models.start_ontology_validation_response_content import StartOntologyValidationResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of StartOntologyValidationResponseContent from a JSON string
start_ontology_validation_response_content_instance = StartOntologyValidationResponseContent.from_json(json)
# print the JSON string representation of the object
print(StartOntologyValidationResponseContent.to_json())

# convert the object into a dict
start_ontology_validation_response_content_dict = start_ontology_validation_response_content_instance.to_dict()
# create an instance of StartOntologyValidationResponseContent from a dict
start_ontology_validation_response_content_from_dict = StartOntologyValidationResponseContent.from_dict(start_ontology_validation_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


