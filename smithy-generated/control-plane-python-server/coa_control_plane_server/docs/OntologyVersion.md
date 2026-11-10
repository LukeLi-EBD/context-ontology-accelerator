# OntologyVersion

One T-Box version row, as the registry stores it.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Version identifier. | 
**semver** | **str** | Semantic version, e.g. &#x60;1.2.0&#x60; or &#x60;1.2.0+rollback.1&#x60;. | 
**status** | [**OntologyVersionStatus**](OntologyVersionStatus.md) |  | 
**content_hash** | **str** | SHA-256 of the canonical graph. | [optional] 
**triple_count** | **float** | Declared triple count of the version. | [optional] 
**format** | **str** | Source serialisation (&#x60;turtle&#x60; or &#x60;nt&#x60;). | [optional] 
**graph** | **str** | Graph IRI holding the version&#39;s triples. | [optional] 
**rollback_of** | **str** | When set, the version was created by rolling back to this version. | [optional] 
**label** | **str** | Human-readable label. | [optional] 
**created_at** | **str** | Creation time (ISO-8601). | [optional] 
**published_at** | **str** | First publish time (ISO-8601); absent while never published. | [optional] 

## Example

```python
from coa_control_plane_server.models.ontology_version import OntologyVersion

# TODO update the JSON string below
json = "{}"
# create an instance of OntologyVersion from a JSON string
ontology_version_instance = OntologyVersion.from_json(json)
# print the JSON string representation of the object
print(OntologyVersion.to_json())

# convert the object into a dict
ontology_version_dict = ontology_version_instance.to_dict()
# create an instance of OntologyVersion from a dict
ontology_version_from_dict = OntologyVersion.from_dict(ontology_version_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


