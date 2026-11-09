# DatabricksSqlWarehouseConfiguration

Databricks SQL Warehouse source — the DATABRICKS_SQL_WAREHOUSE sub-type. Discovery and queries both run through Athena against a connector Lambda this service deploys, which resolves this configuration from the Athena catalog name it is invoked under. Nothing here is deployed by the customer.  Its own shape rather than an extra DatabaseEngine on JdbcConfiguration, whose @required `host`/`port` have no meaning for a warehouse addressed by an HTTP path and which has no place for the Unity Catalog catalog.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_hostname** | **str** | Databricks workspace host, e.g. &#x60;dbc-a1b2345c-d6e7.cloud.databricks.com&#x60;. A PrivateLink-only workspace is not reachable: the connector runs outside any customer VPC. | 
**http_path** | **str** | SQL Warehouse HTTP path. The Databricks analogue of a port. | 
**databricks_catalog** | **str** | Unity Catalog catalog pinned for this source. Lowercased at registration: &#x60;information_schema&#x60; stores identifiers lowercase. | 
**database_name** | **str** | Unity Catalog schema this source exposes. Exactly one per source — the same one-database-per-source model GlueConfiguration and CustomConnectorConfiguration use. Lowercased at registration. | 
**credential_secret_arn** | **str** | Secret holding {\&quot;token\&quot;: ...} for a personal access token, or {\&quot;client_id\&quot;: ..., \&quot;client_secret\&quot;: ...} for OAuth machine-to-machine. The shape selects the auth mode, so a customer cannot declare one mode and store the other. Reachable only through crossAccountRoleArn, so its ACCOUNT is unconstrained; it must be readable by that role and live in the deployment region (Athena does not support cross-Region federated queries).  Note an AWS constraint this service can neither impose nor relax: a secret in a different account from the role must be encrypted with a CUSTOMER-MANAGED key, because &#x60;aws/secretsmanager&#x60; cannot be shared across accounts by any policy. | 
**cross_account_role_arn** | **str** | Customer-owned IAM role the connector assumes to read credentialSecretArn. Same member name, type and meaning as on JdbcConfiguration and GlueConfiguration, and @required here rather than optional: the connector holds no Secrets Manager permission of its own, so there is no direct-read fallback.  Its trust policy must name the connector role and condition on NamespaceDetail$datasourceExternalId; its permission policy grants GetSecretValue on that one secret, plus kms:Decrypt if the secret uses a customer-managed key.  The role MUST be named {RESOURCE_PREFIX}datasource-access-*, because this deployment&#39;s assume grant is scoped to that prefix, so registration rejects any other name explicitly rather than letting it fail as an opaque AccessDenied at first scan. Its ACCOUNT is unconstrained.  There is no externalId member: a caller-supplied ExternalId is the vulnerability it was meant to close, so the value is derived from the namespace. | 
**table_filter** | **str** | Include-filter applied to table names within databaseName. Omit to discover every table. | [optional] 
**table_exclude_filter** | **str** | Exclude-filter applied to table names within databaseName, evaluated after tableFilter. | [optional] 

## Example

```python
from coa_control_plane_server.models.databricks_sql_warehouse_configuration import DatabricksSqlWarehouseConfiguration

# TODO update the JSON string below
json = "{}"
# create an instance of DatabricksSqlWarehouseConfiguration from a JSON string
databricks_sql_warehouse_configuration_instance = DatabricksSqlWarehouseConfiguration.from_json(json)
# print the JSON string representation of the object
print(DatabricksSqlWarehouseConfiguration.to_json())

# convert the object into a dict
databricks_sql_warehouse_configuration_dict = databricks_sql_warehouse_configuration_instance.to_dict()
# create an instance of DatabricksSqlWarehouseConfiguration from a dict
databricks_sql_warehouse_configuration_from_dict = DatabricksSqlWarehouseConfiguration.from_dict(databricks_sql_warehouse_configuration_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


