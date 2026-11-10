# ShaclReport

Outcome of the SHACL gate.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | One of &#x60;&#x60;ok&#x60;&#x60;, &#x60;&#x60;violations&#x60;&#x60;, &#x60;&#x60;skipped&#x60;&#x60;, &#x60;&#x60;error&#x60;&#x60;. | 
**violations** | **float** | Number of violations; null when the gate did not run. | [optional] 
**conforms** | **bool** | True only when the gate ran and produced no violations. | [optional] 
**detail** | **str** | Reason the gate was skipped or errored. | [optional] 

## Example

```python
from coa_control_plane_server.models.shacl_report import ShaclReport

# TODO update the JSON string below
json = "{}"
# create an instance of ShaclReport from a JSON string
shacl_report_instance = ShaclReport.from_json(json)
# print the JSON string representation of the object
print(ShaclReport.to_json())

# convert the object into a dict
shacl_report_dict = shacl_report_instance.to_dict()
# create an instance of ShaclReport from a dict
shacl_report_from_dict = ShaclReport.from_dict(shacl_report_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


