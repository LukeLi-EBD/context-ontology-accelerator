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
import type { UpdateSourceMetadataInput, UpdateSourceMetadataOutput } from "../models/models_0";
import { UpdateSourceMetadata$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UpdateSourceMetadataCommand}.
 */
export interface UpdateSourceMetadataCommandInput extends UpdateSourceMetadataInput {}
/**
 * @public
 *
 * The output of {@link UpdateSourceMetadataCommand}.
 */
export interface UpdateSourceMetadataCommandOutput extends UpdateSourceMetadataOutput, __MetadataBearer {}

/**
 * Update mutable metadata fields on an existing source (DATABASE only).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, UpdateSourceMetadataCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, UpdateSourceMetadataCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // UpdateSourceMetadataInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   name: "STRING_VALUE",
 *   glueConfiguration: { // GlueConfiguration
 *     catalogId: "STRING_VALUE", // required
 *     region: "STRING_VALUE", // required
 *     databaseName: "STRING_VALUE", // required
 *     tableFilter: "STRING_VALUE",
 *     tableExcludeFilter: "STRING_VALUE",
 *     crossAccountRoleArn: "STRING_VALUE",
 *     externalId: "STRING_VALUE",
 *     athenaDataCatalogName: "STRING_VALUE",
 *     executionEngine: "ATHENA" || "REDSHIFT",
 *     redshiftWorkgroup: "STRING_VALUE",
 *   },
 *   jdbcConfiguration: { // JdbcConfiguration
 *     engine: "POSTGRESQL" || "MYSQL" || "REDSHIFT" || "ORACLE" || "SQLSERVER" || "SNOWFLAKE", // required
 *     host: "STRING_VALUE", // required
 *     port: Number("int"), // required
 *     databaseName: "STRING_VALUE", // required
 *     schemaFilter: "STRING_VALUE",
 *     schemaExcludeFilter: "STRING_VALUE",
 *     tableFilter: "STRING_VALUE",
 *     tableExcludeFilter: "STRING_VALUE",
 *     credentialSecretArn: "STRING_VALUE",
 *     crossAccountRoleArn: "STRING_VALUE",
 *     externalId: "STRING_VALUE",
 *     warehouse: "STRING_VALUE",
 *     role: "STRING_VALUE",
 *   },
 *   customConnectorConfiguration: { // CustomConnectorConfiguration
 *     connectorFunctionArn: "STRING_VALUE", // required
 *     databaseName: "STRING_VALUE", // required
 *     tableFilter: "STRING_VALUE",
 *     tableExcludeFilter: "STRING_VALUE",
 *   },
 *   metadataEnrichmentEnabled: true || false,
 * };
 * const command = new UpdateSourceMetadataCommand(input);
 * const response = await client.send(command);
 * // { // UpdateSourceMetadataOutput
 * //   sourceId: "STRING_VALUE", // required
 * //   status: "REGISTERED" || "SCANNING" || "SCANNING_ENTITY_EXTRACTION" || "SCANNING_KG_BUILD" || "ENRICHING" || "PENDING_REVIEW" || "RESCAN_REVIEW" || "APPROVING" || "APPROVAL_FAILED" || "REJECTING" || "REJECTION_FAILED" || "COMPLETED" || "APPROVED" || "REJECTED" || "SCAN_FAILED" || "DELETING" || "DELETED" || "DELETE_FAILED", // required
 * //   updatedAt: new Date("TIMESTAMP"), // required
 * // };
 *
 * ```
 *
 * @param UpdateSourceMetadataCommandInput - {@link UpdateSourceMetadataCommandInput}
 * @returns {@link UpdateSourceMetadataCommandOutput}
 * @see {@link UpdateSourceMetadataCommandInput} for command's `input` shape.
 * @see {@link UpdateSourceMetadataCommandOutput} for command's `response` shape.
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
 * @example Rename a source and enable metadata enrichment
 * ```javascript
 * //
 * const input = {
 *   metadataEnrichmentEnabled: true,
 *   name: "Sales Warehouse (Prod)",
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new UpdateSourceMetadataCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   sourceId: "src-7f3a9c1e",
 *   status: "PENDING_REVIEW",
 *   updatedAt: "2026-07-23T15:00:00Z"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class UpdateSourceMetadataCommand extends $Command
  .classBuilder<
    UpdateSourceMetadataCommandInput,
    UpdateSourceMetadataCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "UpdateSourceMetadata", {})
  .n("ControlPlaneServiceClient", "UpdateSourceMetadataCommand")
  .sc(UpdateSourceMetadata$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: UpdateSourceMetadataInput;
      output: UpdateSourceMetadataOutput;
    };
    sdk: {
      input: UpdateSourceMetadataCommandInput;
      output: UpdateSourceMetadataCommandOutput;
    };
  };
}
