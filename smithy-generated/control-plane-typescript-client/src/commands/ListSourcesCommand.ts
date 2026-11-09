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
import type { ListSourcesInput, ListSourcesOutput } from "../models/models_0";
import { ListSources$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListSourcesCommand}.
 */
export interface ListSourcesCommandInput extends ListSourcesInput {}
/**
 * @public
 *
 * The output of {@link ListSourcesCommand}.
 */
export interface ListSourcesCommandOutput extends ListSourcesOutput, __MetadataBearer {}

/**
 * List all sources in a namespace across all source types.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListSourcesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListSourcesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListSourcesInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceType: "DATABASE" || "DOCUMENTS",
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListSourcesCommand(input);
 * const response = await client.send(command);
 * // { // ListSourcesOutput
 * //   nextToken: "STRING_VALUE",
 * //   items: [ // SourceSummaryList // required
 * //     { // SourceSummary
 * //       sourceId: "STRING_VALUE", // required
 * //       namespaceId: "STRING_VALUE", // required
 * //       name: "STRING_VALUE", // required
 * //       sourceType: "DATABASE" || "DOCUMENTS", // required
 * //       sourceSubType: "GLUE_DATABASE" || "JDBC_DATABASE" || "CUSTOM_CONNECTOR" || "DATABRICKS_SQL_WAREHOUSE" || "RDF_SPARQL" || "S3" || "LOCAL_UPLOAD", // required
 * //       status: "REGISTERED" || "SCANNING" || "SCANNING_ENTITY_EXTRACTION" || "SCANNING_KG_BUILD" || "ENRICHING" || "PENDING_REVIEW" || "RESCAN_REVIEW" || "APPROVING" || "APPROVAL_FAILED" || "REJECTING" || "REJECTION_FAILED" || "COMPLETED" || "APPROVED" || "REJECTED" || "SCAN_FAILED" || "DELETING" || "DELETED" || "DELETE_FAILED", // required
 * //       createdAt: new Date("TIMESTAMP"), // required
 * //       updatedAt: new Date("TIMESTAMP"),
 * //       tablesDiscovered: Number("int"),
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListSourcesCommandInput - {@link ListSourcesCommandInput}
 * @returns {@link ListSourcesCommandOutput}
 * @see {@link ListSourcesCommandInput} for command's `input` shape.
 * @see {@link ListSourcesCommandOutput} for command's `response` shape.
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
 * @example List the database sources in a namespace
 * ```javascript
 * //
 * const input = {
 *   maxResults: 20,
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceType: "DATABASE"
 * };
 * const command = new ListSourcesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   items: [
 *     {
 *       createdAt: "2026-07-23T14:30:00Z",
 *       name: "Sales Warehouse",
 *       namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *       sourceId: "src-7f3a9c1e",
 *       sourceSubType: "GLUE_DATABASE",
 *       sourceType: "DATABASE",
 *       status: "PENDING_REVIEW",
 *       tablesDiscovered: 12,
 *       updatedAt: "2026-07-23T14:35:00Z"
 *     }
 *   ],
 *   nextToken: "eyJvZmZzZXQiOiAyMH0="
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListSourcesCommand extends $Command
  .classBuilder<
    ListSourcesCommandInput,
    ListSourcesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListSources", {})
  .n("ControlPlaneServiceClient", "ListSourcesCommand")
  .sc(ListSources$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListSourcesInput;
      output: ListSourcesOutput;
    };
    sdk: {
      input: ListSourcesCommandInput;
      output: ListSourcesCommandOutput;
    };
  };
}
