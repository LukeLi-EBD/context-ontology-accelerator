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
import type { RejectProposalsInput, RejectProposalsOutput } from "../models/models_1";
import { RejectProposals$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RejectProposalsCommand}.
 */
export interface RejectProposalsCommandInput extends RejectProposalsInput {}
/**
 * @public
 *
 * The output of {@link RejectProposalsCommand}.
 */
export interface RejectProposalsCommandOutput extends RejectProposalsOutput, __MetadataBearer {}

/**
 * Reject one or more proposals.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RejectProposalsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RejectProposalsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RejectProposalsInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalIds: [ // ProposalIdList // required
 *     "STRING_VALUE",
 *   ],
 *   reason: "STRING_VALUE", // required
 * };
 * const command = new RejectProposalsCommand(input);
 * const response = await client.send(command);
 * // { // RejectProposalsOutput
 * //   rejected: Number("int"), // required
 * // };
 *
 * ```
 *
 * @param RejectProposalsCommandInput - {@link RejectProposalsCommandInput}
 * @returns {@link RejectProposalsCommandOutput}
 * @see {@link RejectProposalsCommandInput} for command's `input` shape.
 * @see {@link RejectProposalsCommandOutput} for command's `response` shape.
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
 * @example Reject two proposals with a reason
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalIds: [
 *     "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *     "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 *   ],
 *   reason: "Duplicate of the accepted sales ontology"
 * };
 * const command = new RejectProposalsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   rejected: 2
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RejectProposalsCommand extends $Command
  .classBuilder<
    RejectProposalsCommandInput,
    RejectProposalsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RejectProposals", {})
  .n("ControlPlaneServiceClient", "RejectProposalsCommand")
  .sc(RejectProposals$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RejectProposalsInput;
      output: RejectProposalsOutput;
    };
    sdk: {
      input: RejectProposalsCommandInput;
      output: RejectProposalsCommandOutput;
    };
  };
}
