# BusinessMetadataOutput

Business-facing metadata for a table or column returned in responses: description, synonyms, glossary terms, tags, enrichment source, review status, and AI-inference confidence.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**description** | **str** | Human-readable description of the table or column. | [optional] 
**synonyms** | **List[str]** | Alternative names or aliases. | [optional] 
**glossary_terms** | **List[str]** | Associated business glossary terms. | [optional] 
**tags** | **List[str]** | Free-form classification tags. | [optional] 
**enrichment_source** | **str** | Origin of this metadata (e.g. AI-inferred, steward-specified, catalog-existing). | [optional] 
**review_status** | [**ReviewStatus**](ReviewStatus.md) |  | [optional] 
**confidence** | **float** | AI-inference confidence (0.0-1.0) for AI-generated metadata; absent or 0 for steward-specified or catalog-existing metadata. | [optional] 

## Example

```python
from coa_control_plane_server.models.business_metadata_output import BusinessMetadataOutput

# TODO update the JSON string below
json = "{}"
# create an instance of BusinessMetadataOutput from a JSON string
business_metadata_output_instance = BusinessMetadataOutput.from_json(json)
# print the JSON string representation of the object
print(BusinessMetadataOutput.to_json())

# convert the object into a dict
business_metadata_output_dict = business_metadata_output_instance.to_dict()
# create an instance of BusinessMetadataOutput from a dict
business_metadata_output_from_dict = BusinessMetadataOutput.from_dict(business_metadata_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


