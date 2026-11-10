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
import type { ValidateProposalInput, ValidateProposalOutput } from "../models/models_1";
import { ValidateProposal$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ValidateProposalCommand}.
 */
export interface ValidateProposalCommandInput extends ValidateProposalInput {}
/**
 * @public
 *
 * The output of {@link ValidateProposalCommand}.
 */
export interface ValidateProposalCommandOutput extends ValidateProposalOutput, __MetadataBearer {}

/**
 * Trigger validation of a proposal — runs the configured tier validators
 * (HermiT reasoning, structural metrics, OoPS!) and returns a job ID for
 * polling. Each call starts a new job; send a `clientToken` to make a retry
 * safe.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ValidateProposalCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ValidateProposalCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ValidateProposalInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 *   tiers: [ // ProposalValidationTierList
 *     "tier1_blocking" || "tier2_scoring" || "tier3_review",
 *   ],
 *   shaclShapesTurtle: "STRING_VALUE",
 *   competencyQuestions: [ // CompetencyQuestionList
 *     "STRING_VALUE",
 *   ],
 *   clientToken: "STRING_VALUE",
 * };
 * const command = new ValidateProposalCommand(input);
 * const response = await client.send(command);
 * // { // ValidateProposalOutput
 * //   jobId: "STRING_VALUE", // required
 * //   proposalId: "STRING_VALUE", // required
 * //   status: "pending" || "running" || "completed" || "failed", // required
 * //   createdAt: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param ValidateProposalCommandInput - {@link ValidateProposalCommandInput}
 * @returns {@link ValidateProposalCommandOutput}
 * @see {@link ValidateProposalCommandInput} for command's `input` shape.
 * @see {@link ValidateProposalCommandOutput} for command's `response` shape.
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
 * @example Validate a proposal across all tiers
 * ```javascript
 * //
 * const input = {
 *   competencyQuestions: [
 *     "Which customers placed orders in Q3?"
 *   ],
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   tiers: [
 *     "tier1_blocking",
 *     "tier2_scoring",
 *     "tier3_review"
 *   ]
 * };
 * const command = new ValidateProposalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   createdAt: "2026-07-23T14:30:00Z",
 *   jobId: "c5e8f2b3-7d4a-4f0c-9b3e-6a1d8c2f4e0b",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   status: "pending"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ValidateProposalCommand extends $Command
  .classBuilder<
    ValidateProposalCommandInput,
    ValidateProposalCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ValidateProposal", {})
  .n("ControlPlaneServiceClient", "ValidateProposalCommand")
  .sc(ValidateProposal$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ValidateProposalInput;
      output: ValidateProposalOutput;
    };
    sdk: {
      input: ValidateProposalCommandInput;
      output: ValidateProposalCommandOutput;
    };
  };
}
