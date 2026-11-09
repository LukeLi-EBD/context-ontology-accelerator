# DescribeSchemaResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**classes** | [**List[SchemaClass]**](SchemaClass.md) | The classes in the namespace&#39;s schema. | 
**ontology_version** | **str** | Version of the ontology described. | [optional] 

## Example

```python
from coa_data_layer_server.models.describe_schema_response_content import DescribeSchemaResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of DescribeSchemaResponseContent from a JSON string
describe_schema_response_content_instance = DescribeSchemaResponseContent.from_json(json)
# print the JSON string representation of the object
print(DescribeSchemaResponseContent.to_json())

# convert the object into a dict
describe_schema_response_content_dict = describe_schema_response_content_instance.to_dict()
# create an instance of DescribeSchemaResponseContent from a dict
describe_schema_response_content_from_dict = DescribeSchemaResponseContent.from_dict(describe_schema_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


