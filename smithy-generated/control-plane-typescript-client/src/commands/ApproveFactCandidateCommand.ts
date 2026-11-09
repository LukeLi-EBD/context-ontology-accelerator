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
import type { ApproveFactCandidateInput, ApproveFactCandidateOutput } from "../models/models_0";
import { ApproveFactCandidate$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ApproveFactCandidateCommand}.
 */
export interface ApproveFactCandidateCommandInput extends ApproveFactCandidateInput {}
/**
 * @public
 *
 * The output of {@link ApproveFactCandidateCommand}.
 */
export interface ApproveFactCandidateCommandOutput extends ApproveFactCandidateOutput, __MetadataBearer {}

/**
 * Approve a candidate: write the fact to the ledger and project it into the
 * namespace A-Box graph. Idempotent per candidate; a second approval answers
 * 409 with the fact id already written.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ApproveFactCandidateCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ApproveFactCandidateCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ApproveFactCandidateInput
 *   namespaceId: "STRING_VALUE", // required
 *   candidateId: "STRING_VALUE", // required
 *   actor: "STRING_VALUE",
 *   factOverrides: { // FactOverrides
 *     "<keys>": "STRING_VALUE",
 *   },
 * };
 * const command = new ApproveFactCandidateCommand(input);
 * const response = await client.send(command);
 * // { // ApproveFactCandidateOutput
 * //   factId: "STRING_VALUE", // required
 * //   status: "PENDING" || "APPROVED" || "REJECTED", // required
 * // };
 *
 * ```
 *
 * @param ApproveFactCandidateCommandInput - {@link ApproveFactCandidateCommandInput}
 * @returns {@link ApproveFactCandidateCommandOutput}
 * @see {@link ApproveFactCandidateCommandInput} for command's `input` shape.
 * @see {@link ApproveFactCandidateCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Approve a candidate
 * ```javascript
 * //
 * const input = {
 *   candidateId: "3c4d5e6f-7081-492a-8b3c-4d5e6f708192",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new ApproveFactCandidateCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   factId: "4d5e6f70-8192-4a3b-9c4d-5e6f708192a3",
 *   status: "APPROVED"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ApproveFactCandidateCommand extends $Command
  .classBuilder<
    ApproveFactCandidateCommandInput,
    ApproveFactCandidateCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ApproveFactCandidate", {})
  .n("ControlPlaneServiceClient", "ApproveFactCandidateCommand")
  .sc(ApproveFactCandidate$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ApproveFactCandidateInput;
      output: ApproveFactCandidateOutput;
    };
    sdk: {
      input: ApproveFactCandidateCommandInput;
      output: ApproveFactCandidateCommandOutput;
    };
  };
}
