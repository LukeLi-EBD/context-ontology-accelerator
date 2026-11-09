# GlueConfiguration

Glue Data Catalog database connection configuration.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**catalog_id** | **str** | Glue Data Catalog id: a 12-digit AWS account id (the account&#39;s root catalog) or a nested catalog id of the form &#x60;account:catalogName&#x60; (federated / S3 Tables / Redshift-backed / cross-account catalogs). | 
**region** | **str** | AWS region identifier. | 
**database_name** | **str** | Database name. | 
**table_filter** | **str** | Passed to Glue &#x60;GetTables&#x60; as its native &#x60;Expression&#x60; (a regular expression) — the one filter that is not a glob. | [optional] 
**table_exclude_filter** | **str** | Tables matching this glob filter are excluded. | [optional] 
**cross_account_role_arn** | **str** | IAM role ARN for cross-account access. | [optional] 
**external_id** | **str** | IGNORED. The ExternalId presented on the cross-account assume is derived from the namespace (&#x60;NamespaceDetail$datasourceExternalId&#x60;) and is no longer accepted from the request: a caller-chosen value would hand back control of what binds the assume to its namespace. Sources onboarded before this change keep the value already stored on their record. This shape is deprecated since 2026-08-28: Ignored. Condition the role&#39;s trust policy on NamespaceDetail$datasourceExternalId instead. | [optional] 
**athena_data_catalog_name** | **str** | Nested Athena/Glue catalog name when the database lives in a federated or other non-root catalog. When set, the source is queried as &#x60;AwsDataCatalog.&lt;athenaDataCatalogName&gt;.&lt;databaseName&gt;.&lt;table&gt;&#x60;; when omitted, as &#x60;AwsDataCatalog.&lt;databaseName&gt;.&lt;table&gt;&#x60;. | [optional] 
**execution_engine** | [**GlueExecutionEngine**](GlueExecutionEngine.md) |  | [optional] 
**redshift_workgroup** | **str** | Redshift Serverless workgroup used to execute queries when &#x60;executionEngine&#x60; is REDSHIFT. Ignored (and unnecessary) for ATHENA. | [optional] 

## Example

```python
from coa_control_plane_server.models.glue_configuration import GlueConfiguration

# TODO update the JSON string below
json = "{}"
# create an instance of GlueConfiguration from a JSON string
glue_configuration_instance = GlueConfiguration.from_json(json)
# print the JSON string representation of the object
print(GlueConfiguration.to_json())

# convert the object into a dict
glue_configuration_dict = glue_configuration_instance.to_dict()
# create an instance of GlueConfiguration from a dict
glue_configuration_from_dict = GlueConfiguration.from_dict(glue_configuration_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


