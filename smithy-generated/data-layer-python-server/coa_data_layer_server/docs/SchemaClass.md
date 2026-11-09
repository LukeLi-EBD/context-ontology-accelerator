# SchemaClass

A class in the namespace's queryable schema, with its IRI, label, optional description, properties, and parent class.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | IRI identifying the class. | 
**label** | **str** | Human-readable label for the class. | 
**description** | **str** | Description of the class. | [optional] 
**properties** | [**List[SchemaProperty]**](SchemaProperty.md) | Properties defined on the class. | [optional] 
**parent_class** | **str** | IRI of the parent class, if any. | [optional] 

## Example

```python
from coa_data_layer_server.models.schema_class import SchemaClass

# TODO update the JSON string below
json = "{}"
# create an instance of SchemaClass from a JSON string
schema_class_instance = SchemaClass.from_json(json)
# print the JSON string representation of the object
print(SchemaClass.to_json())

# convert the object into a dict
schema_class_dict = schema_class_instance.to_dict()
# create an instance of SchemaClass from a dict
schema_class_from_dict = SchemaClass.from_dict(schema_class_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


