// smithy-typescript generated code
import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { Command as $Command } from "@smithy/smithy-client";
import type { MetadataBearer as __MetadataBearer } from "@smithy/types";

import type {
  ControlPlaneServiceClientResolvedConfig,
  ServiceInputTypes,
  ServiceOutputTypes,
} from "../ControlPlaneServiceClient";
import { commonParams } from "../endpoint/EndpointParameters";
import type { GetSourceOperationInput, GetSourceOperationOutput } from "../models/models_1";
import { GetSource$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetSourceCommand}.
 */
export interface GetSourceCommandInput extends GetSourceOperationInput {}
/**
 * @public
 *
 * The output of {@link GetSourceCommand}.
 */
export interface GetSourceCommandOutput extends GetSourceOperationOutput, __MetadataBearer {}

/**
 * Get a single source by ID.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetSourceCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetSourceCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetSourceOperationInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 * };
 * const command = new GetSourceCommand(input);
 * const response = await client.send(command);
 * // { // GetSourceOperationOutput
 * //   body: { // GetSourceOutput
 * //     sourceId: "STRING_VALUE", // required
 * //     namespaceId: "STRING_VALUE", // required
 * //     name: "STRING_VALUE", // required
 * //     sourceType: "DATABASE" || "DOCUMENTS", // required
 * //     sourceSubType: "GLUE_DATABASE" || "JDBC_DATABASE" || "CUSTOM_CONNECTOR" || "DATABRICKS_SQL_WAREHOUSE" || "RDF_SPARQL" || "S3" || "LOCAL_UPLOAD", // required
 * //     status: "REGISTERED" || "SCANNING" || "SCANNING_ENTITY_EXTRACTION" || "SCANNING_KG_BUILD" || "ENRICHING" || "PENDING_REVIEW" || "RESCAN_REVIEW" || "APPROVING" || "APPROVAL_FAILED" || "REJECTING" || "REJECTION_FAILED" || "COMPLETED" || "APPROVED" || "REJECTED" || "SCAN_FAILED" || "DELETING" || "DELETED" || "DELETE_FAILED", // required
 * //     createdAt: new Date("TIMESTAMP"), // required
 * //     updatedAt: new Date("TIMESTAMP"),
 * //     databaseDetails: { // DatabaseSourceDetail
 * //       glueConfiguration: { // GlueConfiguration
 * //         catalogId: "STRING_VALUE", // required
 * //         region: "STRING_VALUE", // required
 * //         databaseName: "STRING_VALUE", // required
 * //         tableFilter: "STRING_VALUE",
 * //         tableExcludeFilter: "STRING_VALUE",
 * //         crossAccountRoleArn: "STRING_VALUE",
 * //         externalId: "STRING_VALUE",
 * //         athenaDataCatalogName: "STRING_VALUE",
 * //         executionEngine: "ATHENA" || "REDSHIFT",
 * //         redshiftWorkgroup: "STRING_VALUE",
 * //       },
 * //       jdbcConfiguration: { // JdbcConfiguration
 * //         engine: "POSTGRESQL" || "MYSQL" || "REDSHIFT" || "ORACLE" || "SQLSERVER" || "SNOWFLAKE", // required
 * //         host: "STRING_VALUE", // required
 * //         port: Number("int"), // required
 * //         databaseName: "STRING_VALUE", // required
 * //         schemaFilter: "STRING_VALUE",
 * //         schemaExcludeFilter: "STRING_VALUE",
 * //         tableFilter: "STRING_VALUE",
 * //         tableExcludeFilter: "STRING_VALUE",
 * //         credentialSecretArn: "STRING_VALUE",
 * //         crossAccountRoleArn: "STRING_VALUE",
 * //         externalId: "STRING_VALUE",
 * //         warehouse: "STRING_VALUE",
 * //         role: "STRING_VALUE",
 * //       },
 * //       customConnectorConfiguration: { // CustomConnectorConfiguration
 * //         connectorFunctionArn: "STRING_VALUE", // required
 * //         databaseName: "STRING_VALUE", // required
 * //         tableFilter: "STRING_VALUE",
 * //         tableExcludeFilter: "STRING_VALUE",
 * //       },
 * //       databricksSqlWarehouseConfiguration: { // DatabricksSqlWarehouseConfiguration
 * //         workspaceHostname: "STRING_VALUE", // required
 * //         httpPath: "STRING_VALUE", // required
 * //         databricksCatalog: "STRING_VALUE", // required
 * //         databaseName: "STRING_VALUE", // required
 * //         credentialSecretArn: "STRING_VALUE", // required
 * //         crossAccountRoleArn: "STRING_VALUE", // required
 * //         tableFilter: "STRING_VALUE",
 * //         tableExcludeFilter: "STRING_VALUE",
 * //       },
 * //       sparqlConfiguration: { // SparqlConfiguration
 * //         store: "neptune",
 * //         dataEndpoint: "STRING_VALUE", // required
 * //         region: "STRING_VALUE",
 * //         port: Number("int"),
 * //         dataNamedGraph: "STRING_VALUE",
 * //         authMode: "sigv4",
 * //         credentialSecretArn: "STRING_VALUE",
 * //       },
 * //       metadataEnrichmentEnabled: true || false,
 * //       queryEngine: "ATHENA" || "JDBC" || "REDSHIFT",
 * //       tablesDiscovered: Number("int"),
 * //       tablesApproved: Number("int"),
 * //       lastScanJobId: "STRING_VALUE",
 * //       lastScanAt: new Date("TIMESTAMP"),
 * //       glueConnectionName: "STRING_VALUE",
 * //       athenaDataCatalogName: "STRING_VALUE",
 * //       rescanSchedule: { // RescanSchedule
 * //         enabled: true || false, // required
 * //         scheduleExpression: "STRING_VALUE",
 * //         timezone: "STRING_VALUE",
 * //       },
 * //       eventRescan: { // EventRescanConfig
 * //         enabled: true || false, // required
 * //       },
 * //     },
 * //     documentDetails: { // DocumentSourceDetail
 * //       s3Prefixes: [ // S3PrefixList
 * //         "STRING_VALUE",
 * //       ],
 * //       sourceBucketArn: "STRING_VALUE",
 * //       roleArn: "STRING_VALUE",
 * //       extractionConfig: { // ExtractionConfig
 * //         extractionMode: "continuous" || "separated",
 * //         useBatchInference: true || false,
 * //         enableVersioning: true || false,
 * //         enablePropositionExtraction: true || false,
 * //         preferredEntityClassifications: [ // EntityClassificationList
 * //           "STRING_VALUE",
 * //         ],
 * //         inferEntityClassifications: true || false,
 * //         preferredTopics: [ // TopicList
 * //           "STRING_VALUE",
 * //         ],
 * //         enableTableExtraction: true || false,
 * //         chunkSize: Number("int"),
 * //         chunkOverlap: Number("int"),
 * //         deletePrevVersions: true || false,
 * //         bedrockModelArn: "STRING_VALUE",
 * //       },
 * //       filesTotal: Number("int"),
 * //       filesSkipped: Number("int"),
 * //       filesErrored: Number("int"),
 * //       errorMessage: "STRING_VALUE",
 * //       preprocessingIssues: [ // PreprocessingIssueList
 * //         { // PreprocessingIssue
 * //           filename: "STRING_VALUE", // required
 * //           type: "skipped" || "error", // required
 * //           reason: "STRING_VALUE", // required
 * //         },
 * //       ],
 * //       documentsProcessed: Number("int"),
 * //       chunksLLM: Number("int"),
 * //       chunksEmbed: Number("int"),
 * //       chunksGraph: Number("int"),
 * //     },
 * //   },
 * // };
 *
 * ```
 *
 * @param GetSourceCommandInput - {@link GetSourceCommandInput}
 * @returns {@link GetSourceCommandOutput}
 * @see {@link GetSourceCommandInput} for command's `input` shape.
 * @see {@link GetSourceCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link InternalServerError} (server fault)
 *  Returned with HTTP 500 when the service fails unexpectedly. The message is a
 * fixed, generic description; the underlying cause is logged, never returned.
 *
 * @throws {@link ServiceUnavailableError} (server fault)
 *  Returned with HTTP 503 when the service, or a required dependency (including
 * one it needs to handle the request safely), is temporarily unavailable. For
 * example, a create that
 * carries a `clientToken` fails closed with this error when the retry-safety
 * store cannot be reached, rather than risk running the create twice. Retry
 * the request (with the same `clientToken`) after a backoff.
 *
 * @throws {@link ControlPlaneServiceServiceException}
 * <p>Base exception class for all service exceptions from ControlPlaneService service.</p>
 *
 *
 * @example Get a Glue database source
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new GetSourceCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   body: {
 *     createdAt: "2026-07-23T14:30:00Z",
 *     databaseDetails: {
 *       glueConfiguration: {
 *         catalogId: "123456789012",
 *         databaseName: "sales",
 *         region: "us-east-1"
 *       },
 *       lastScanAt: "2026-07-23T14:35:00Z",
 *       lastScanJobId: "job-8b21d4f0",
 *       metadataEnrichmentEnabled: true,
 *       queryEngine: "ATHENA",
 *       tablesApproved: 3,
 *       tablesDiscovered: 12
 *     },
 *     name: "Sales Warehouse",
 *     namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *     sourceId: "src-7f3a9c1e",
 *     sourceSubType: "GLUE_DATABASE",
 *     sourceType: "DATABASE",
 *     status: "PENDING_REVIEW",
 *     updatedAt: "2026-07-23T14:35:00Z"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetSourceCommand extends $Command
  .classBuilder<
    GetSourceCommandInput,
    GetSourceCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetSource", {})
  .n("ControlPlaneServiceClient", "GetSourceCommand")
  .sc(GetSource$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetSourceOperationInput;
      output: GetSourceOperationOutput;
    };
    sdk: {
      input: GetSourceCommandInput;
      output: GetSourceCommandOutput;
    };
  };
}
