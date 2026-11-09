# InducedDatasource

Summary of an inducted data source.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**datasource_id** | **str** | Data source identifier reference. | 
**proposal_id** | **str** | UUID v4 identifier. | [optional] 
**ontology_id** | **str** | Ontology ID produced for this data source. | [optional] 
**label** | **str** | Human-readable label for the induction run. | [optional] 
**tables_processed** | **float** | Number of tables processed during induction. | [optional] 
**columns_processed** | **float** | Number of columns processed during induction. | [optional] 
**novel_classes_created** | **float** | Number of novel classes created (not grounded to existing concepts). | [optional] 

## Example

```python
from coa_control_plane_server.models.induced_datasource import InducedDatasource

# TODO update the JSON string below
json = "{}"
# create an instance of InducedDatasource from a JSON string
induced_datasource_instance = InducedDatasource.from_json(json)
# print the JSON string representation of the object
print(InducedDatasource.to_json())

# convert the object into a dict
induced_datasource_dict = induced_datasource_instance.to_dict()
# create an instance of InducedDatasource from a dict
induced_datasource_from_dict = InducedDatasource.from_dict(induced_datasource_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


