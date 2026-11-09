# JdbcConfiguration

JDBC database connection configuration.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**engine** | [**DatabaseEngine**](DatabaseEngine.md) |  | 
**host** | **str** | Database hostname or endpoint. | 
**port** | **float** | Database port number. | 
**database_name** | **str** | Database name. | 
**schema_filter** | **str** | Only schemas matching this glob filter are discovered. | [optional] 
**schema_exclude_filter** | **str** | Schemas matching this glob filter are excluded, IN ADDITION TO the engine&#39;s system schemas (e.g. &#x60;pg_catalog&#x60;, &#x60;information_schema&#x60;), which are always excluded. | [optional] 
**table_filter** | **str** | Schema/table filter: one or more shell globs, separated by &#x60;|&#x60; or &#x60;,&#x60;, each matched against the WHOLE name. &#x60;*&#x60; matches any characters, &#x60;?&#x60; one character, &#x60;[abc]&#x60; one of a set. Examples: &#x60;sales_*&#x60;, &#x60;public|analytics&#x60;, &#x60;constructor*,results&#x60;. Not a regular expression — &#x60;^&#x60;, &#x60;$&#x60; and &#x60;.*&#x60; are matched literally. The one exception is a Glue Data Catalog source&#39;s &#x60;tableFilter&#x60;, which is passed to Glue as its native expression syntax. | [optional] 
**table_exclude_filter** | **str** | Schema/table filter: one or more shell globs, separated by &#x60;|&#x60; or &#x60;,&#x60;, each matched against the WHOLE name. &#x60;*&#x60; matches any characters, &#x60;?&#x60; one character, &#x60;[abc]&#x60; one of a set. Examples: &#x60;sales_*&#x60;, &#x60;public|analytics&#x60;, &#x60;constructor*,results&#x60;. Not a regular expression — &#x60;^&#x60;, &#x60;$&#x60; and &#x60;.*&#x60; are matched literally. The one exception is a Glue Data Catalog source&#39;s &#x60;tableFilter&#x60;, which is passed to Glue as its native expression syntax. | [optional] 
**credential_secret_arn** | **str** | Secrets Manager ARN for database credentials. | [optional] 
**cross_account_role_arn** | **str** | IAM role ARN for cross-account access. | [optional] 
**external_id** | **str** | IGNORED. The ExternalId presented on the cross-account assume is derived from the namespace (&#x60;NamespaceDetail$datasourceExternalId&#x60;) and is no longer accepted from the request: a caller-chosen value would hand back control of what binds the assume to its namespace. Sources onboarded before this change keep the value already stored on their record. This shape is deprecated since 2026-08-28: Ignored. Condition the role&#39;s trust policy on NamespaceDetail$datasourceExternalId instead. | [optional] 
**warehouse** | **str** | Snowflake only: the virtual warehouse used to run INFORMATION_SCHEMA queries during discovery (Snowflake requires an active warehouse). | [optional] 
**role** | **str** | Snowflake only: optional Snowflake RBAC role name to assume for the session (a Snowflake construct — not an AWS IAM role; see crossAccountRoleArn). | [optional] 

## Example

```python
from coa_control_plane_server.models.jdbc_configuration import JdbcConfiguration

# TODO update the JSON string below
json = "{}"
# create an instance of JdbcConfiguration from a JSON string
jdbc_configuration_instance = JdbcConfiguration.from_json(json)
# print the JSON string representation of the object
print(JdbcConfiguration.to_json())

# convert the object into a dict
jdbc_configuration_dict = jdbc_configuration_instance.to_dict()
# create an instance of JdbcConfiguration from a dict
jdbc_configuration_from_dict = JdbcConfiguration.from_dict(jdbc_configuration_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


