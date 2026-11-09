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
import type { AcceptProposalInput, AcceptProposalOutput } from "../models/models_0";
import { AcceptProposal$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link AcceptProposalCommand}.
 */
export interface AcceptProposalCommandInput extends AcceptProposalInput {}
/**
 * @public
 *
 * The output of {@link AcceptProposalCommand}.
 */
export interface AcceptProposalCommandOutput extends AcceptProposalOutput, __MetadataBearer {}

/**
 * Accept a proposal asynchronously — merge its ontology into the target
 * namespace on a background worker. Returns 202 immediately with the
 * proposal flipped to ``accepting``. Clients poll ``GetProposal`` until
 * ``status`` becomes ``accepted`` (success) or ``pending`` (failed —
 * ``acceptError`` on the proposal record carries the reason).
 *
 * Naturally idempotent, so there is no `clientToken`: accepting an
 * already-accepted proposal returns ``accepted`` without starting a new job,
 * and a repeat while the first accept is in progress is a ConflictError (409).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, AcceptProposalCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, AcceptProposalCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // AcceptProposalInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE",
 * };
 * const command = new AcceptProposalCommand(input);
 * const response = await client.send(command);
 * // { // AcceptProposalOutput
 * //   proposalId: "STRING_VALUE", // required
 * //   status: "inducing" || "pending" || "accepting" || "embeddings_sync" || "accepted" || "accept_failed" || "rejected" || "cancelled" || "updated" || "failed", // required
 * // };
 *
 * ```
 *
 * @param AcceptProposalCommandInput - {@link AcceptProposalCommandInput}
 * @returns {@link AcceptProposalCommandOutput}
 * @see {@link AcceptProposalCommandInput} for command's `input` shape.
 * @see {@link AcceptProposalCommandOutput} for command's `response` shape.
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
 * @example Accept a proposal into its target ontology
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "ont-sales-2026",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new AcceptProposalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   status: "accepting"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class AcceptProposalCommand extends $Command
  .classBuilder<
    AcceptProposalCommandInput,
    AcceptProposalCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "AcceptProposal", {})
  .n("ControlPlaneServiceClient", "AcceptProposalCommand")
  .sc(AcceptProposal$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: AcceptProposalInput;
      output: AcceptProposalOutput;
    };
    sdk: {
      input: AcceptProposalCommandInput;
      output: AcceptProposalCommandOutput;
    };
  };
}
