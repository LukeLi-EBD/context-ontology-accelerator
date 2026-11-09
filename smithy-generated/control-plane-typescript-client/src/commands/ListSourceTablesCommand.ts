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
import type { ListSourceTablesInput, ListSourceTablesOutput } from "../models/models_0";
import { ListSourceTables$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListSourceTablesCommand}.
 */
export interface ListSourceTablesCommandInput extends ListSourceTablesInput {}
/**
 * @public
 *
 * The output of {@link ListSourceTablesCommand}.
 */
export interface ListSourceTablesCommandOutput extends ListSourceTablesOutput, __MetadataBearer {}

/**
 * List tables discovered for a DATABASE source with enrichment/review summary.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListSourceTablesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListSourceTablesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListSourceTablesInput
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   reviewStatus: "PENDING_REVIEW" || "APPROVED" || "REJECTED",
 * };
 * const command = new ListSourceTablesCommand(input);
 * const response = await client.send(command);
 * // { // ListSourceTablesOutput
 * //   nextToken: "STRING_VALUE",
 * //   items: [ // TableSummaryList // required
 * //     { // TableSummary
 * //       tableId: "STRING_VALUE", // required
 * //       name: "STRING_VALUE", // required
 * //       database: "STRING_VALUE", // required
 * //       columnCount: Number("int"),
 * //       columnsApproved: Number("int"),
 * //       columnsPendingDeletion: Number("int"),
 * //       pendingRelationships: Number("int"),
 * //       reviewStatus: "PENDING_REVIEW" || "APPROVED" || "REJECTED", // required
 * //       enrichmentSource: "STRING_VALUE",
 * //       pendingDeletion: true || false,
 * //       added: true || false,
 * //     },
 * //   ],
 * //   skippedAssets: Number("int"),
 * // };
 *
 * ```
 *
 * @param ListSourceTablesCommandInput - {@link ListSourceTablesCommandInput}
 * @returns {@link ListSourceTablesCommandOutput}
 * @see {@link ListSourceTablesCommandInput} for command's `input` shape.
 * @see {@link ListSourceTablesCommandOutput} for command's `response` shape.
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
 * @example List tables awaiting review for a source
 * ```javascript
 * //
 * const input = {
 *   maxResults: 20,
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   reviewStatus: "PENDING_REVIEW",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new ListSourceTablesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   items: [
 *     {
 *       columnCount: 8,
 *       columnsApproved: 0,
 *       database: "sales",
 *       enrichmentSource: "AI_GENERATED",
 *       name: "orders",
 *       reviewStatus: "PENDING_REVIEW",
 *       tableId: "sales.orders"
 *     }
 *   ],
 *   nextToken: "eyJvZmZzZXQiOiAyMH0="
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListSourceTablesCommand extends $Command
  .classBuilder<
    ListSourceTablesCommandInput,
    ListSourceTablesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListSourceTables", {})
  .n("ControlPlaneServiceClient", "ListSourceTablesCommand")
  .sc(ListSourceTables$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListSourceTablesInput;
      output: ListSourceTablesOutput;
    };
    sdk: {
      input: ListSourceTablesCommandInput;
      output: ListSourceTablesCommandOutput;
    };
  };
}
