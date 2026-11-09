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
import type { CancelProposalInput, CancelProposalOutput } from "../models/models_0";
import { CancelProposal$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CancelProposalCommand}.
 */
export interface CancelProposalCommandInput extends CancelProposalInput {}
/**
 * @public
 *
 * The output of {@link CancelProposalCommand}.
 */
export interface CancelProposalCommandOutput extends CancelProposalOutput, __MetadataBearer {}

/**
 * Cancel a pending proposal.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, CancelProposalCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, CancelProposalCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // CancelProposalInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 * };
 * const command = new CancelProposalCommand(input);
 * const response = await client.send(command);
 * // { // CancelProposalOutput
 * //   proposalId: "STRING_VALUE", // required
 * //   status: "inducing" || "pending" || "accepting" || "embeddings_sync" || "accepted" || "accept_failed" || "rejected" || "cancelled" || "updated" || "failed", // required
 * // };
 *
 * ```
 *
 * @param CancelProposalCommandInput - {@link CancelProposalCommandInput}
 * @returns {@link CancelProposalCommandOutput}
 * @see {@link CancelProposalCommandInput} for command's `input` shape.
 * @see {@link CancelProposalCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
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
 * @example Cancel a pending proposal
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new CancelProposalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   status: "cancelled"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class CancelProposalCommand extends $Command
  .classBuilder<
    CancelProposalCommandInput,
    CancelProposalCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "CancelProposal", {})
  .n("ControlPlaneServiceClient", "CancelProposalCommand")
  .sc(CancelProposal$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: CancelProposalInput;
      output: CancelProposalOutput;
    };
    sdk: {
      input: CancelProposalCommandInput;
      output: CancelProposalCommandOutput;
    };
  };
}
