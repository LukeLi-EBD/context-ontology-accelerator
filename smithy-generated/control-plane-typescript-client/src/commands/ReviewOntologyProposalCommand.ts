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
import type { OntologyProposalReviewResult, ReviewOntologyProposalInput } from "../models/models_1";
import { ReviewOntologyProposal$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ReviewOntologyProposalCommand}.
 */
export interface ReviewOntologyProposalCommandInput extends ReviewOntologyProposalInput {}
/**
 * @public
 *
 * The output of {@link ReviewOntologyProposalCommand}.
 */
export interface ReviewOntologyProposalCommandOutput extends OntologyProposalReviewResult, __MetadataBearer {}

/**
 * Approve or reject a proposal.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ReviewOntologyProposalCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ReviewOntologyProposalCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ReviewOntologyProposalInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 *   decision: "APPROVE" || "REJECT", // required
 *   comment: "STRING_VALUE",
 *   actor: "STRING_VALUE",
 * };
 * const command = new ReviewOntologyProposalCommand(input);
 * const response = await client.send(command);
 * // { // OntologyProposalReviewResult
 * //   ok: true || false,
 * //   proposalId: "STRING_VALUE", // required
 * //   versionId: "STRING_VALUE",
 * //   status: "proposed" || "review" || "approved" || "published" || "rejected",
 * //   versionStatus: "draft" || "proposed" || "review" || "approved" || "published" || "superseded" || "rejected" || "deprecated",
 * //   approvedBy: "STRING_VALUE",
 * //   approvedAt: "STRING_VALUE",
 * //   reviewedImplicitly: true || false,
 * //   rejectedBy: "STRING_VALUE",
 * //   rejectedAt: "STRING_VALUE",
 * //   reason: "STRING_VALUE",
 * //   unchanged: true || false,
 * // };
 *
 * ```
 *
 * @param ReviewOntologyProposalCommandInput - {@link ReviewOntologyProposalCommandInput}
 * @returns {@link ReviewOntologyProposalCommandOutput}
 * @see {@link ReviewOntologyProposalCommandInput} for command's `input` shape.
 * @see {@link ReviewOntologyProposalCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
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
 * @example Approve a proposal
 * ```javascript
 * //
 * const input = {
 *   actor: "reviewer",
 *   comment: "looks good",
 *   decision: "APPROVE",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core",
 *   proposalId: "prop-1a2b3c4d5e6f"
 * };
 * const command = new ReviewOntologyProposalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   approvedBy: "reviewer",
 *   ok: true,
 *   proposalId: "prop-1a2b3c4d5e6f",
 *   status: "approved",
 *   versionId: "ont-draft-9f8e7d6c5b4a",
 *   versionStatus: "approved"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ReviewOntologyProposalCommand extends $Command
  .classBuilder<
    ReviewOntologyProposalCommandInput,
    ReviewOntologyProposalCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ReviewOntologyProposal", {})
  .n("ControlPlaneServiceClient", "ReviewOntologyProposalCommand")
  .sc(ReviewOntologyProposal$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ReviewOntologyProposalInput;
      output: OntologyProposalReviewResult;
    };
    sdk: {
      input: ReviewOntologyProposalCommandInput;
      output: ReviewOntologyProposalCommandOutput;
    };
  };
}
