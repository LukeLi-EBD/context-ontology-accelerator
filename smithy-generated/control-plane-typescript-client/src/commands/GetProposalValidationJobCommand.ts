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
import type { GetProposalValidationJobInput, GetProposalValidationJobOutput } from "../models/models_0";
import { GetProposalValidationJob$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetProposalValidationJobCommand}.
 */
export interface GetProposalValidationJobCommandInput extends GetProposalValidationJobInput {}
/**
 * @public
 *
 * The output of {@link GetProposalValidationJobCommand}.
 */
export interface GetProposalValidationJobCommandOutput extends GetProposalValidationJobOutput, __MetadataBearer {}

/**
 * Get a proposal validation job.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetProposalValidationJobCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetProposalValidationJobCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetProposalValidationJobInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 *   jobId: "STRING_VALUE", // required
 * };
 * const command = new GetProposalValidationJobCommand(input);
 * const response = await client.send(command);
 * // { // GetProposalValidationJobOutput
 * //   jobId: "STRING_VALUE", // required
 * //   proposalId: "STRING_VALUE", // required
 * //   status: "pending" || "running" || "completed" || "failed", // required
 * //   createdAt: "STRING_VALUE", // required
 * //   error: "STRING_VALUE",
 * //   report: { // ProposalValidationReport
 * //     jobId: "STRING_VALUE", // required
 * //     proposalId: "STRING_VALUE", // required
 * //     passed: true || false, // required
 * //     findings: [ // ProposalValidationFindingList // required
 * //       { // ProposalValidationFinding
 * //         validator: "STRING_VALUE", // required
 * //         tier: "tier1_blocking" || "tier2_scoring" || "tier3_review", // required
 * //         severity: "error" || "warning" || "info", // required
 * //         code: "STRING_VALUE", // required
 * //         message: "STRING_VALUE", // required
 * //         subject: "STRING_VALUE",
 * //         details: "DOCUMENT_VALUE",
 * //       },
 * //     ],
 * //     tiersRun: [ // ProposalValidationTierList // required
 * //       "tier1_blocking" || "tier2_scoring" || "tier3_review",
 * //     ],
 * //     createdAt: "STRING_VALUE", // required
 * //   },
 * // };
 *
 * ```
 *
 * @param GetProposalValidationJobCommandInput - {@link GetProposalValidationJobCommandInput}
 * @returns {@link GetProposalValidationJobCommandOutput}
 * @see {@link GetProposalValidationJobCommandInput} for command's `input` shape.
 * @see {@link GetProposalValidationJobCommandOutput} for command's `response` shape.
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
 * @example Get a completed validation job with its report
 * ```javascript
 * //
 * const input = {
 *   jobId: "c5e8f2b3-7d4a-4f0c-9b3e-6a1d8c2f4e0b",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new GetProposalValidationJobCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   createdAt: "2026-07-23T14:30:00Z",
 *   jobId: "c5e8f2b3-7d4a-4f0c-9b3e-6a1d8c2f4e0b",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   report: {
 *     createdAt: "2026-07-23T14:30:00Z",
 *     findings: [
 *       {
 *         code: "UNSAT_CLASS_RISK",
 *         message: "Class Order has a disjointness that may cause unsatisfiability",
 *         severity: "warning",
 *         subject: "https://ontology.example.com/sales/Order",
 *         tier: "tier1_blocking",
 *         validator: "hermit"
 *       }
 *     ],
 *     jobId: "c5e8f2b3-7d4a-4f0c-9b3e-6a1d8c2f4e0b",
 *     passed: false,
 *     proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *     tiersRun: [
 *       "tier1_blocking",
 *       "tier2_scoring",
 *       "tier3_review"
 *     ]
 *   },
 *   status: "completed"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetProposalValidationJobCommand extends $Command
  .classBuilder<
    GetProposalValidationJobCommandInput,
    GetProposalValidationJobCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetProposalValidationJob", {})
  .n("ControlPlaneServiceClient", "GetProposalValidationJobCommand")
  .sc(GetProposalValidationJob$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetProposalValidationJobInput;
      output: GetProposalValidationJobOutput;
    };
    sdk: {
      input: GetProposalValidationJobCommandInput;
      output: GetProposalValidationJobCommandOutput;
    };
  };
}
