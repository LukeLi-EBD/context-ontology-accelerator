# DatabaseSourceDetail

Type-specific detail for DATABASE sources.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**glue_configuration** | [**GlueConfiguration**](GlueConfiguration.md) |  | [optional] 
**jdbc_configuration** | [**JdbcConfiguration**](JdbcConfiguration.md) |  | [optional] 
**custom_connector_configuration** | [**CustomConnectorConfiguration**](CustomConnectorConfiguration.md) |  | [optional] 
**databricks_sql_warehouse_configuration** | [**DatabricksSqlWarehouseConfiguration**](DatabricksSqlWarehouseConfiguration.md) |  | [optional] 
**sparql_configuration** | [**SparqlConfiguration**](SparqlConfiguration.md) |  | [optional] 
**metadata_enrichment_enabled** | **bool** | Whether AI-powered business metadata enrichment runs for this source. Set at creation time and persisted with the source record. When false the scan pipeline skips the enrichment step and the source transitions from SCANNING straight to PENDING_REVIEW. | [optional] 
**query_engine** | [**QueryEngine**](QueryEngine.md) |  | [optional] 
**tables_discovered** | **float** | Number of tables discovered in the most recent scan. | [optional] 
**tables_approved** | **float** | Number of tables with reviewStatus&#x3D;APPROVED. | [optional] 
**last_scan_job_id** | **str** | Identifier of the most recent scan job. | [optional] 
**last_scan_at** | **float** | Timestamp of the most recent scan. | [optional] 
**glue_connection_name** | **str** | Name of the Glue Connection that backs Athena federated queries for this data source. Read-only and system-managed: populated only for JDBC sub-types (PostgreSQL, MySQL, Redshift, Oracle, SQL Server, Snowflake) on first scan and removed when the source is deleted. Null for S3/Iceberg-backed Glue databases — those are queried via Athena&#39;s native AwsDataCatalog.  To query the source via Athena, pair this with the namespace&#39;s &#x60;athenaWorkgroupName&#x60; and the &#x60;athenaDataCatalogName&#x60; below. See the Athena Queryability section of &#x60;packages/sources/README.md&#x60; for examples. | [optional] 
**athena_data_catalog_name** | **str** | Name of the Athena data catalog registered for this source. Read-only and system-managed, derived from &#x60;{resource-prefix}ds_{sourceId}&#x60;. Null for S3/Iceberg-backed Glue databases, which are queried through Athena&#39;s native &#x60;AwsDataCatalog&#x60;.  The addressing differs by sub-type, because the two catalogs are not the same kind of object:  - JDBC sub-types: a managed Glue federated catalog, NESTED under   &#x60;AwsDataCatalog&#x60;, and equal to &#x60;glueConnectionName&#x60;. Query it as   &#x60;AwsDataCatalog.&lt;athenaDataCatalogName&gt;.&lt;schema&gt;.&lt;table&gt;&#x60;. - CUSTOM_CONNECTOR: a LAMBDA-type Athena catalog bound to the customer&#39;s   connector Lambda. It is a TOP-LEVEL catalog, not nested, so query it as   &#x60;&lt;athenaDataCatalogName&gt;.&lt;databaseName&gt;.&lt;table&gt;&#x60;. - DATABRICKS_SQL_WAREHOUSE: also a TOP-LEVEL LAMBDA-type catalog, addressed   the same way, but bound to the ONE connector Lambda this deployment   operates — every such catalog in the environment shares that handler ARN,   and the catalog name is what selects the source&#39;s workspace and   credential. &#x60;databaseName&#x60; is the Unity Catalog schema.  Run the query inside the namespace&#39;s Athena workgroup (see NamespaceDetail.athenaWorkgroupName). | [optional] 
**rescan_schedule** | [**RescanSchedule**](RescanSchedule.md) |  | [optional] 
**event_rescan** | [**EventRescanConfig**](EventRescanConfig.md) |  | [optional] 

## Example

```python
from coa_control_plane_server.models.database_source_detail import DatabaseSourceDetail

# TODO update the JSON string below
json = "{}"
# create an instance of DatabaseSourceDetail from a JSON string
database_source_detail_instance = DatabaseSourceDetail.from_json(json)
# print the JSON string representation of the object
print(DatabaseSourceDetail.to_json())

# convert the object into a dict
database_source_detail_dict = database_source_detail_instance.to_dict()
# create an instance of DatabaseSourceDetail from a dict
database_source_detail_from_dict = DatabaseSourceDetail.from_dict(database_source_detail_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


