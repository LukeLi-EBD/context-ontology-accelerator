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
import type { ReviewSourceColumnInput, ReviewSourceColumnOutput } from "../models/models_1";
import { ReviewSourceColumn$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ReviewSourceColumnCommand}.
 */
export interface ReviewSourceColumnCommandInput extends ReviewSourceColumnInput {}
/**
 * @public
 *
 * The output of {@link ReviewSourceColumnCommand}.
 */
export interface ReviewSourceColumnCommandOutput extends ReviewSourceColumnOutput, __MetadataBearer {}

/**
 * Review a single column on a table — set reviewStatus to APPROVED or REJECTED.
 *
 * DataZone asset revision is only written when the resulting status differs
 * from the existing one.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ReviewSourceColumnCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ReviewSourceColumnCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ReviewSourceColumnInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   tableId: "STRING_VALUE", // required
 *   columnName: "STRING_VALUE", // required
 *   decision: "APPROVED" || "REJECTED", // required
 * };
 * const command = new ReviewSourceColumnCommand(input);
 * const response = await client.send(command);
 * // { // ReviewSourceColumnOutput
 * //   tableId: "STRING_VALUE", // required
 * //   columnName: "STRING_VALUE", // required
 * //   reviewStatus: "PENDING_REVIEW" || "APPROVED" || "REJECTED", // required
 * // };
 *
 * ```
 *
 * @param ReviewSourceColumnCommandInput - {@link ReviewSourceColumnCommandInput}
 * @returns {@link ReviewSourceColumnCommandOutput}
 * @see {@link ReviewSourceColumnCommandInput} for command's `input` shape.
 * @see {@link ReviewSourceColumnCommandOutput} for command's `response` shape.
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
 * @example Reject a single column
 * ```javascript
 * //
 * const input = {
 *   columnName: "internal_notes",
 *   decision: "REJECTED",
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e",
 *   tableId: "sales.orders"
 * };
 * const command = new ReviewSourceColumnCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   columnName: "internal_notes",
 *   reviewStatus: "REJECTED",
 *   tableId: "sales.orders"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ReviewSourceColumnCommand extends $Command
  .classBuilder<
    ReviewSourceColumnCommandInput,
    ReviewSourceColumnCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ReviewSourceColumn", {})
  .n("ControlPlaneServiceClient", "ReviewSourceColumnCommand")
  .sc(ReviewSourceColumn$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ReviewSourceColumnInput;
      output: ReviewSourceColumnOutput;
    };
    sdk: {
      input: ReviewSourceColumnCommandInput;
      output: ReviewSourceColumnCommandOutput;
    };
  };
}
