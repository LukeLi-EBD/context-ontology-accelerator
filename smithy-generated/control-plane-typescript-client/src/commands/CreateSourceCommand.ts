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
import type { CreateSourceOperationInput, CreateSourceOperationOutput } from "../models/models_0";
import { CreateSource$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CreateSourceCommand}.
 */
export interface CreateSourceCommandInput extends CreateSourceOperationInput {}
/**
 * @public
 *
 * The output of {@link CreateSourceCommand}.
 */
export interface CreateSourceCommandOutput extends CreateSourceOperationOutput, __MetadataBearer {}

/**
 * Create a new source.
 * The body must contain sourceType plus exactly one of:
 *   databaseSource  — when sourceType = DATABASE
 *   documentSource  — when sourceType = DOCUMENTS
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, CreateSourceCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, CreateSourceCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // CreateSourceOperationInput
 *   namespaceId: "STRING_VALUE", // required
 *   body: { // CreateSourceInput
 *     sourceType: "DATABASE" || "DOCUMENTS", // required
 *     databaseSource: { // CreateDatabaseSourceInput
 *       name: "STRING_VALUE", // required
 *       glueConfiguration: { // GlueConfiguration
 *         catalogId: "STRING_VALUE", // required
 *         region: "STRING_VALUE", // required
 *         databaseName: "STRING_VALUE", // required
 *         tableFilter: "STRING_VALUE",
 *         tableExcludeFilter: "STRING_VALUE",
 *         crossAccountRoleArn: "STRING_VALUE",
 *         externalId: "STRING_VALUE",
 *         athenaDataCatalogName: "STRING_VALUE",
 *         executionEngine: "ATHENA" || "REDSHIFT",
 *         redshiftWorkgroup: "STRING_VALUE",
 *       },
 *       jdbcConfiguration: { // JdbcConfiguration
 *         engine: "POSTGRESQL" || "MYSQL" || "REDSHIFT" || "ORACLE" || "SQLSERVER" || "SNOWFLAKE", // required
 *         host: "STRING_VALUE", // required
 *         port: Number("int"), // required
 *         databaseName: "STRING_VALUE", // required
 *         schemaFilter: "STRING_VALUE",
 *         schemaExcludeFilter: "STRING_VALUE",
 *         tableFilter: "STRING_VALUE",
 *         tableExcludeFilter: "STRING_VALUE",
 *         credentialSecretArn: "STRING_VALUE",
 *         crossAccountRoleArn: "STRING_VALUE",
 *         externalId: "STRING_VALUE",
 *         warehouse: "STRING_VALUE",
 *         role: "STRING_VALUE",
 *       },
 *       customConnectorConfiguration: { // CustomConnectorConfiguration
 *         connectorFunctionArn: "STRING_VALUE", // required
 *         databaseName: "STRING_VALUE", // required
 *         tableFilter: "STRING_VALUE",
 *         tableExcludeFilter: "STRING_VALUE",
 *       },
 *       databricksSqlWarehouseConfiguration: { // DatabricksSqlWarehouseConfiguration
 *         workspaceHostname: "STRING_VALUE", // required
 *         httpPath: "STRING_VALUE", // required
 *         databricksCatalog: "STRING_VALUE", // required
 *         databaseName: "STRING_VALUE", // required
 *         credentialSecretArn: "STRING_VALUE", // required
 *         crossAccountRoleArn: "STRING_VALUE", // required
 *         tableFilter: "STRING_VALUE",
 *         tableExcludeFilter: "STRING_VALUE",
 *       },
 *       sparqlConfiguration: { // SparqlConfiguration
 *         store: "neptune",
 *         dataEndpoint: "STRING_VALUE", // required
 *         region: "STRING_VALUE",
 *         port: Number("int"),
 *         dataNamedGraph: "STRING_VALUE",
 *         authMode: "sigv4",
 *         credentialSecretArn: "STRING_VALUE",
 *       },
 *       metadataEnrichmentEnabled: true || false,
 *     },
 *     documentSource: { // CreateDocumentSourceInput
 *       name: "STRING_VALUE", // required
 *       s3Prefixes: [ // S3PrefixList
 *         "STRING_VALUE",
 *       ],
 *       uploadId: "STRING_VALUE",
 *       sourceBucketArn: "STRING_VALUE",
 *       roleArn: "STRING_VALUE",
 *       extractionConfig: { // ExtractionConfig
 *         extractionMode: "continuous" || "separated",
 *         useBatchInference: true || false,
 *         enableVersioning: true || false,
 *         enablePropositionExtraction: true || false,
 *         preferredEntityClassifications: [ // EntityClassificationList
 *           "STRING_VALUE",
 *         ],
 *         inferEntityClassifications: true || false,
 *         preferredTopics: [ // TopicList
 *           "STRING_VALUE",
 *         ],
 *         enableTableExtraction: true || false,
 *         chunkSize: Number("int"),
 *         chunkOverlap: Number("int"),
 *         deletePrevVersions: true || false,
 *         bedrockModelArn: "STRING_VALUE",
 *       },
 *     },
 *     clientToken: "STRING_VALUE",
 *   },
 * };
 * const command = new CreateSourceCommand(input);
 * const response = await client.send(command);
 * // { // CreateSourceOperationOutput
 * //   body: { // CreateSourceOutput
 * //     sourceId: "STRING_VALUE", // required
 * //     status: "REGISTERED" || "SCANNING" || "SCANNING_ENTITY_EXTRACTION" || "SCANNING_KG_BUILD" || "ENRICHING" || "PENDING_REVIEW" || "RESCAN_REVIEW" || "APPROVING" || "APPROVAL_FAILED" || "REJECTING" || "REJECTION_FAILED" || "COMPLETED" || "APPROVED" || "REJECTED" || "SCAN_FAILED" || "DELETING" || "DELETED" || "DELETE_FAILED", // required
 * //     scanJobId: "STRING_VALUE",
 * //     createdAt: new Date("TIMESTAMP"), // required
 * //   },
 * // };
 *
 * ```
 *
 * @param CreateSourceCommandInput - {@link CreateSourceCommandInput}
 * @returns {@link CreateSourceCommandOutput}
 * @see {@link CreateSourceCommandInput} for command's `input` shape.
 * @see {@link CreateSourceCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Register a Glue Data Catalog database source
 * ```javascript
 * //
 * const input = {
 *   body: {
 *     databaseSource: {
 *       glueConfiguration: {
 *         catalogId: "123456789012",
 *         databaseName: "sales",
 *         region: "us-east-1",
 *         tableFilter: "orders.*"
 *       },
 *       metadataEnrichmentEnabled: true,
 *       name: "Sales Warehouse"
 *     },
 *     sourceType: "DATABASE"
 *   },
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
 * };
 * const command = new CreateSourceCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   body: {
 *     createdAt: "2026-07-23T14:30:00Z",
 *     scanJobId: "job-8b21d4f0",
 *     sourceId: "src-7f3a9c1e",
 *     status: "SCANNING"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class CreateSourceCommand extends $Command
  .classBuilder<
    CreateSourceCommandInput,
    CreateSourceCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "CreateSource", {})
  .n("ControlPlaneServiceClient", "CreateSourceCommand")
  .sc(CreateSource$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: CreateSourceOperationInput;
      output: CreateSourceOperationOutput;
    };
    sdk: {
      input: CreateSourceCommandInput;
      output: CreateSourceCommandOutput;
    };
  };
}
