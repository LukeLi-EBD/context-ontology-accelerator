# SchemaProperty

A property of a schema class, with its IRI, label, value range (datatype or target class), and optional description.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | IRI identifying the property. | 
**label** | **str** | Human-readable label for the property. | 
**range** | **str** | Value range of the property (datatype or target class). | [optional] 
**description** | **str** | Description of the property. | [optional] 

## Example

```python
from coa_data_layer_server.models.schema_property import SchemaProperty

# TODO update the JSON string below
json = "{}"
# create an instance of SchemaProperty from a JSON string
schema_property_instance = SchemaProperty.from_json(json)
# print the JSON string representation of the object
print(SchemaProperty.to_json())

# convert the object into a dict
schema_property_dict = schema_property_instance.to_dict()
# create an instance of SchemaProperty from a dict
schema_property_from_dict = SchemaProperty.from_dict(schema_property_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


