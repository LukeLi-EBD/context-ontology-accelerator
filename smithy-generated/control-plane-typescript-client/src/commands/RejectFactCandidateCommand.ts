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
import type { RejectFactCandidateInput, RejectFactCandidateOutput } from "../models/models_0";
import { RejectFactCandidate$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RejectFactCandidateCommand}.
 */
export interface RejectFactCandidateCommandInput extends RejectFactCandidateInput {}
/**
 * @public
 *
 * The output of {@link RejectFactCandidateCommand}.
 */
export interface RejectFactCandidateCommandOutput extends RejectFactCandidateOutput, __MetadataBearer {}

/**
 * Reject a candidate. The row is kept for audit; nothing is written to the
 * fact ledger or the A-Box graph.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RejectFactCandidateCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RejectFactCandidateCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RejectFactCandidateInput
 *   namespaceId: "STRING_VALUE", // required
 *   candidateId: "STRING_VALUE", // required
 *   actor: "STRING_VALUE",
 *   reason: "STRING_VALUE", // required
 * };
 * const command = new RejectFactCandidateCommand(input);
 * const response = await client.send(command);
 * // { // RejectFactCandidateOutput
 * //   status: "PENDING" || "APPROVED" || "REJECTED", // required
 * // };
 *
 * ```
 *
 * @param RejectFactCandidateCommandInput - {@link RejectFactCandidateCommandInput}
 * @returns {@link RejectFactCandidateCommandOutput}
 * @see {@link RejectFactCandidateCommandInput} for command's `input` shape.
 * @see {@link RejectFactCandidateCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
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
 * @example Reject a candidate
 * ```javascript
 * //
 * const input = {
 *   candidateId: "3c4d5e6f-7081-492a-8b3c-4d5e6f708192",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   reason: "Predicate is too generic to publish."
 * };
 * const command = new RejectFactCandidateCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   status: "REJECTED"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RejectFactCandidateCommand extends $Command
  .classBuilder<
    RejectFactCandidateCommandInput,
    RejectFactCandidateCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RejectFactCandidate", {})
  .n("ControlPlaneServiceClient", "RejectFactCandidateCommand")
  .sc(RejectFactCandidate$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RejectFactCandidateInput;
      output: RejectFactCandidateOutput;
    };
    sdk: {
      input: RejectFactCandidateCommandInput;
      output: RejectFactCandidateCommandOutput;
    };
  };
}
