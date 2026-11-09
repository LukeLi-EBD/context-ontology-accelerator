# DimensionFilter

A filter constraining a query to rows matching a dimension value, with an optional comparison operator (defaults to equality).  Server-side invariants NOT expressible as Smithy traits, enforced at validation (a violation is a 400, see the Context Manager's InvokeRequest):   - `name` must be non-blank, and is trimmed before use.   - `name` is matched case-insensitively, and must be UNIQUE across the list —     a mapping cannot express two values for one dimension. (`@uniqueItems`     would not capture this: it compares whole structures, so two filters on     the same name with different values would still pass.)   - every filter must be applicable by the resolved metric; a filter the     metric cannot apply fails closed rather than being dropped.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Name of the dimension to filter on. | 
**value** | **str** | Value to match for the dimension. For compatibility, the server also accepts a JSON number (finite) or boolean here and binds it as a typed literal; &#x60;null&#x60;, objects, and arrays are rejected. | 
**operator** | [**DimensionOperator**](DimensionOperator.md) |  | [optional] 

## Example

```python
from coa_data_layer_server.models.dimension_filter import DimensionFilter

# TODO update the JSON string below
json = "{}"
# create an instance of DimensionFilter from a JSON string
dimension_filter_instance = DimensionFilter.from_json(json)
# print the JSON string representation of the object
print(DimensionFilter.to_json())

# convert the object into a dict
dimension_filter_dict = dimension_filter_instance.to_dict()
# create an instance of DimensionFilter from a dict
dimension_filter_from_dict = DimensionFilter.from_dict(dimension_filter_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


