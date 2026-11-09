# CustomConnectorConfiguration

Custom Athena Query Federation connector configuration — the CUSTOM_CONNECTOR sub-type. The connector is a Lambda the customer authors and deploys in their own account, which this service registers as a Lambda-backed Athena data catalog in its own account; both discovery and serve-time queries run through Athena against that catalog.  Unlike GlueConfiguration there is no Glue database behind the source, so there is no catalogId and no cross-account IAM role to assume: the customer grants access on the connector Lambda's own resource policy instead. There is also no region member — the connector must live in this deployment's region (see connectorFunctionArn).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**connector_function_arn** | **str** | ARN of the connector Lambda. ONE Lambda serves both metadata and record requests — what Athena calls a composite handler. The ARN&#39;s region must equal this deployment&#39;s own region, because Athena can only invoke a data-source connector co-located with the query.  Athena also accepts a split metadata/record PAIR of Lambdas, which this member was once one half of. The pair is deliberately not modelled: the reference connector and the CDK template customers are given both deploy a single composite Lambda, so a second ARN asked every customer to reason about a distinction almost none of them would make — and an ARN placed in the wrong one of two adjacent members fails at query time rather than at onboarding. Restoring it is purely additive (one optional member, plus the record-function catalog parameter) if a customer ever needs the split form. | 
**database_name** | **str** | The single database inside the connector&#39;s catalog that this source exposes. Exactly one database is resolved per source, so a connector serving several databases is onboarded once per database. | 
**table_filter** | **str** | Include-filter applied to table names within databaseName. Omit to discover every table. | [optional] 
**table_exclude_filter** | **str** | Exclude-filter applied to table names within databaseName, evaluated after tableFilter. | [optional] 

## Example

```python
from coa_control_plane_server.models.custom_connector_configuration import CustomConnectorConfiguration

# TODO update the JSON string below
json = "{}"
# create an instance of CustomConnectorConfiguration from a JSON string
custom_connector_configuration_instance = CustomConnectorConfiguration.from_json(json)
# print the JSON string representation of the object
print(CustomConnectorConfiguration.to_json())

# convert the object into a dict
custom_connector_configuration_dict = custom_connector_configuration_instance.to_dict()
# create an instance of CustomConnectorConfiguration from a dict
custom_connector_configuration_from_dict = CustomConnectorConfiguration.from_dict(custom_connector_configuration_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


