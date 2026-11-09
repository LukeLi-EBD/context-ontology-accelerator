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
import type { ReviewSourceTableInput, ReviewSourceTableOutput } from "../models/models_0";
import { ReviewSourceTable$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ReviewSourceTableCommand}.
 */
export interface ReviewSourceTableCommandInput extends ReviewSourceTableInput {}
/**
 * @public
 *
 * The output of {@link ReviewSourceTableCommand}.
 */
export interface ReviewSourceTableCommandOutput extends ReviewSourceTableOutput, __MetadataBearer {}

/**
 * Review a single table — set reviewStatus to APPROVED or REJECTED.
 *
 * Cascades to PENDING columns on that table only (REJECTED columns are not
 * touched). DataZone asset revision is only written when the resulting
 * status differs from the existing one.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ReviewSourceTableCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ReviewSourceTableCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ReviewSourceTableInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   tableId: "STRING_VALUE", // required
 *   decision: "APPROVED" || "REJECTED", // required
 * };
 * const command = new ReviewSourceTableCommand(input);
 * const response = await client.send(command);
 * // { // ReviewSourceTableOutput
 * //   tableId: "STRING_VALUE", // required
 * //   reviewStatus: "PENDING_REVIEW" || "APPROVED" || "REJECTED", // required
 * // };
 *
 * ```
 *
 * @param ReviewSourceTableCommandInput - {@link ReviewSourceTableCommandInput}
 * @returns {@link ReviewSourceTableCommandOutput}
 * @see {@link ReviewSourceTableCommandInput} for command's `input` shape.
 * @see {@link ReviewSourceTableCommandOutput} for command's `response` shape.
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
 * @example Approve a single table
 * ```javascript
 * //
 * const input = {
 *   decision: "APPROVED",
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e",
 *   tableId: "sales.orders"
 * };
 * const command = new ReviewSourceTableCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   reviewStatus: "APPROVED",
 *   tableId: "sales.orders"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ReviewSourceTableCommand extends $Command
  .classBuilder<
    ReviewSourceTableCommandInput,
    ReviewSourceTableCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ReviewSourceTable", {})
  .n("ControlPlaneServiceClient", "ReviewSourceTableCommand")
  .sc(ReviewSourceTable$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ReviewSourceTableInput;
      output: ReviewSourceTableOutput;
    };
    sdk: {
      input: ReviewSourceTableCommandInput;
      output: ReviewSourceTableCommandOutput;
    };
  };
}
