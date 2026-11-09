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
import type { UpdateProposalInput, UpdateProposalOutput } from "../models/models_0";
import { UpdateProposal$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UpdateProposalCommand}.
 */
export interface UpdateProposalCommandInput extends UpdateProposalInput {}
/**
 * @public
 *
 * The output of {@link UpdateProposalCommand}.
 */
export interface UpdateProposalCommandOutput extends UpdateProposalOutput, __MetadataBearer {}

/**
 * Update a proposal's Turtle/R2RML content (user revision).
 *
 * Uses ``POST /update`` with proposalId in the body rather than
 * ``PATCH /\{proposalId\}`` because PATCH ergonomics are awkward with
 * API Gateway request validation here. Either Turtle artifact may be
 * independently revised.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, UpdateProposalCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, UpdateProposalCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // UpdateProposalInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 *   ontologyTurtle: "STRING_VALUE",
 *   r2rmlTurtle: "STRING_VALUE",
 *   groundingOverrides: { // GroundingOverrideMap
 *     "<keys>": "STRING_VALUE",
 *   },
 *   novelTables: [ // GroundingNovelTableList
 *     "STRING_VALUE",
 *   ],
 *   ontologyUploaded: true || false,
 *   r2rmlUploaded: true || false,
 *   uploadRevisionId: "STRING_VALUE",
 * };
 * const command = new UpdateProposalCommand(input);
 * const response = await client.send(command);
 * // { // UpdateProposalOutput
 * //   proposalId: "STRING_VALUE", // required
 * //   status: "inducing" || "pending" || "accepting" || "embeddings_sync" || "accepted" || "accept_failed" || "rejected" || "cancelled" || "updated" || "failed", // required
 * // };
 *
 * ```
 *
 * @param UpdateProposalCommandInput - {@link UpdateProposalCommandInput}
 * @returns {@link UpdateProposalCommandOutput}
 * @see {@link UpdateProposalCommandInput} for command's `input` shape.
 * @see {@link UpdateProposalCommandOutput} for command's `response` shape.
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
 * @throws {@link ServiceUnavailableError} (server fault)
 *  Returned with HTTP 503 when the service, or a required dependency (including
 * one it needs to handle the request safely), is temporarily unavailable. For
 * example, a create that
 * carries a `clientToken` fails closed with this error when the retry-safety
 * store cannot be reached, rather than risk running the create twice. Retry
 * the request (with the same `clientToken`) after a backoff.
 *
 * @throws {@link InternalServerError} (server fault)
 *  Returned with HTTP 500 when the service fails unexpectedly. The message is a
 * fixed, generic description; the underlying cause is logged, never returned.
 *
 * @throws {@link ControlPlaneServiceServiceException}
 * <p>Base exception class for all service exceptions from ControlPlaneService service.</p>
 *
 *
 * @example Revise a proposal's OWL Turtle inline
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyTurtle: `@prefix : <https://ontology.example.com/sales/> .
 * :Order a owl:Class ;
 *     rdfs:label "Order" .`,
 *   ontologyUploaded: false,
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   r2rmlUploaded: false
 * };
 * const command = new UpdateProposalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   status: "updated"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class UpdateProposalCommand extends $Command
  .classBuilder<
    UpdateProposalCommandInput,
    UpdateProposalCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "UpdateProposal", {})
  .n("ControlPlaneServiceClient", "UpdateProposalCommand")
  .sc(UpdateProposal$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: UpdateProposalInput;
      output: UpdateProposalOutput;
    };
    sdk: {
      input: UpdateProposalCommandInput;
      output: UpdateProposalCommandOutput;
    };
  };
}
