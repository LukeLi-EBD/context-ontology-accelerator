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
import type { UpdateSourceColumnMetadataInput, UpdateSourceColumnMetadataOutput } from "../models/models_0";
import { UpdateSourceColumnMetadata$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UpdateSourceColumnMetadataCommand}.
 */
export interface UpdateSourceColumnMetadataCommandInput extends UpdateSourceColumnMetadataInput {}
/**
 * @public
 *
 * The output of {@link UpdateSourceColumnMetadataCommand}.
 */
export interface UpdateSourceColumnMetadataCommandOutput extends UpdateSourceColumnMetadataOutput, __MetadataBearer {}

/**
 * Edit a single column's business metadata. Sets
 * enrichmentSource = STEWARD_EDITED. Does NOT change reviewStatus.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, UpdateSourceColumnMetadataCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, UpdateSourceColumnMetadataCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // UpdateSourceColumnMetadataInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   tableId: "STRING_VALUE", // required
 *   columnName: "STRING_VALUE", // required
 *   overrides: { // MetadataOverrides
 *     description: "STRING_VALUE",
 *     synonyms: [ // MetadataTermList
 *       "STRING_VALUE",
 *     ],
 *     glossaryTerms: [
 *       "STRING_VALUE",
 *     ],
 *     tags: [
 *       "STRING_VALUE",
 *     ],
 *   },
 * };
 * const command = new UpdateSourceColumnMetadataCommand(input);
 * const response = await client.send(command);
 * // { // UpdateSourceColumnMetadataOutput
 * //   tableId: "STRING_VALUE", // required
 * //   columnName: "STRING_VALUE", // required
 * //   reviewStatus: "PENDING_REVIEW" || "APPROVED" || "REJECTED", // required
 * // };
 *
 * ```
 *
 * @param UpdateSourceColumnMetadataCommandInput - {@link UpdateSourceColumnMetadataCommandInput}
 * @returns {@link UpdateSourceColumnMetadataCommandOutput}
 * @see {@link UpdateSourceColumnMetadataCommandInput} for command's `input` shape.
 * @see {@link UpdateSourceColumnMetadataCommandOutput} for command's `response` shape.
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
 * @example Edit a column's business metadata
 * ```javascript
 * //
 * const input = {
 *   columnName: "order_total",
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   overrides: {
 *     description: "Order grand total in USD, including tax",
 *     glossaryTerms: [
 *       "Revenue"
 *     ],
 *     synonyms: [
 *       "order amount",
 *       "grand total"
 *     ],
 *     tags: [
 *       "currency-usd"
 *     ]
 *   },
 *   sourceId: "src-7f3a9c1e",
 *   tableId: "sales.orders"
 * };
 * const command = new UpdateSourceColumnMetadataCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   columnName: "order_total",
 *   reviewStatus: "PENDING_REVIEW",
 *   tableId: "sales.orders"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class UpdateSourceColumnMetadataCommand extends $Command
  .classBuilder<
    UpdateSourceColumnMetadataCommandInput,
    UpdateSourceColumnMetadataCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "UpdateSourceColumnMetadata", {})
  .n("ControlPlaneServiceClient", "UpdateSourceColumnMetadataCommand")
  .sc(UpdateSourceColumnMetadata$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: UpdateSourceColumnMetadataInput;
      output: UpdateSourceColumnMetadataOutput;
    };
    sdk: {
      input: UpdateSourceColumnMetadataCommandInput;
      output: UpdateSourceColumnMetadataCommandOutput;
    };
  };
}
