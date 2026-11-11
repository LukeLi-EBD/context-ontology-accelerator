# OntologyValidationReport

Result of a completed job.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** | Job this report belongs to. | 
**ontology_id** | **str** | Ontology the job validated. | [optional] 
**passed** | **bool** | True only when no finding has severity &#x60;error&#x60;. | 
**findings** | [**List[OntologyValidationFinding]**](OntologyValidationFinding.md) | Every finding across the requested tiers. | 
**metrics** | [**OntologyValidationMetrics**](OntologyValidationMetrics.md) |  | [optional] 
**tiers_run** | [**List[OntologyValidationTier]**](OntologyValidationTier.md) | Tiers that actually ran. | 
**created_at** | **str** | When the report was produced (ISO-8601). | 

## Example

```python
from coa_control_plane_server.models.ontology_validation_report import OntologyValidationReport

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyValidationReport from a JSON string
ontology_validation_report_instance = OntologyValidationReport.from_json(json)
# print the JSON string representation of the object
print(OntologyValidationReport.to_json())

# convert the object into a dict
ontology_validation_report_dict = ontology_validation_report_instance.to_dict()
# create an instance of OntologyValidationReport from a dict
ontology_validation_report_from_dict = OntologyValidationReport.from_dict(ontology_validation_report_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


