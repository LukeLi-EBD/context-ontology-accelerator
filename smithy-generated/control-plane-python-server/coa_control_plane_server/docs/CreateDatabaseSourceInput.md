# CreateDatabaseSourceInput

Database source creation fields. Exactly one of glueConfiguration, jdbcConfiguration, customConnectorConfiguration, databricksSqlWarehouseConfiguration or sparqlConfiguration must be provided — it selects the sub-type.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Human-readable display name. Allows spaces and punctuation. 1–128 chars. | 
**glue_configuration** | [**GlueConfiguration**](GlueConfiguration.md) |  | [optional] 
**jdbc_configuration** | [**JdbcConfiguration**](JdbcConfiguration.md) |  | [optional] 
**custom_connector_configuration** | [**CustomConnectorConfiguration**](CustomConnectorConfiguration.md) |  | [optional] 
**databricks_sql_warehouse_configuration** | [**DatabricksSqlWarehouseConfiguration**](DatabricksSqlWarehouseConfiguration.md) |  | [optional] 
**sparql_configuration** | [**SparqlConfiguration**](SparqlConfiguration.md) |  | [optional] 
**metadata_enrichment_enabled** | **bool** | Enable AI-powered business metadata enrichment (descriptions, synonyms, glossary terms, tags). Defaults to true. When false the scan pipeline skips the enrichment step and the source transitions directly from SCANNING to PENDING_REVIEW with discovered technical metadata only. | [optional] 

## Example

```python
from coa_control_plane_server.models.create_database_source_input import CreateDatabaseSourceInput

# TODO update the JSON string below
json = "{}"
# create an instance of CreateDatabaseSourceInput from a JSON string
create_database_source_input_instance = CreateDatabaseSourceInput.from_json(json)
# print the JSON string representation of the object
print(CreateDatabaseSourceInput.to_json())

# convert the object into a dict
create_database_source_input_dict = create_database_source_input_instance.to_dict()
# create an instance of CreateDatabaseSourceInput from a dict
create_database_source_input_from_dict = CreateDatabaseSourceInput.from_dict(create_database_source_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


