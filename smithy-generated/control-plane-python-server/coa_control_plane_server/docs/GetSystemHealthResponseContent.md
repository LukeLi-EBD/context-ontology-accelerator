# GetSystemHealthResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Overall system status: \&quot;ok\&quot; or \&quot;degraded\&quot; | 
**ontology_induction** | [**OntologyInductionHealth**](OntologyInductionHealth.md) |  | [optional] 
**dynamodb** | **str** | DynamoDB sources table status | [optional] 
**neptune_kg** | **str** | Neptune KG (GraphRAG) status | [optional] 
**opensearch** | **str** | OpenSearch Serverless collection status | [optional] 

## Example

```python
from coa_control_plane_server.models.get_system_health_response_content import GetSystemHealthResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetSystemHealthResponseContent from a JSON string
get_system_health_response_content_instance = GetSystemHealthResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetSystemHealthResponseContent.to_json())

# convert the object into a dict
get_system_health_response_content_dict = get_system_health_response_content_instance.to_dict()
# create an instance of GetSystemHealthResponseContent from a dict
get_system_health_response_content_from_dict = GetSystemHealthResponseContent.from_dict(get_system_health_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


