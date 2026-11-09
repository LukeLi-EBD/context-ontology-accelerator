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
import type { GetProposalInput, GetProposalOutput } from "../models/models_0";
import { GetProposal$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetProposalCommand}.
 */
export interface GetProposalCommandInput extends GetProposalInput {}
/**
 * @public
 *
 * The output of {@link GetProposalCommand}.
 */
export interface GetProposalCommandOutput extends GetProposalOutput, __MetadataBearer {}

/**
 * Get a specific proposal with full ontology content.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetProposalCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetProposalCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetProposalInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 * };
 * const command = new GetProposalCommand(input);
 * const response = await client.send(command);
 * // { // GetProposalOutput
 * //   proposalId: "STRING_VALUE", // required
 * //   status: "inducing" || "pending" || "accepting" || "embeddings_sync" || "accepted" || "accept_failed" || "rejected" || "cancelled" || "updated" || "failed", // required
 * //   ontologyId: "STRING_VALUE", // required
 * //   ontologyTurtle: "STRING_VALUE",
 * //   r2rmlTurtle: "STRING_VALUE",
 * //   ontologyUrl: "STRING_VALUE",
 * //   r2rmlUrl: "STRING_VALUE",
 * //   matchesUrl: "STRING_VALUE",
 * //   constraintsUrl: "STRING_VALUE",
 * //   metadata: { // ProposalMetadata
 * //     datasourceIds: [ // DataSourceIdList
 * //       "STRING_VALUE",
 * //     ],
 * //     label: "STRING_VALUE",
 * //     tablesProcessed: Number("int"),
 * //     columnsProcessed: Number("int"),
 * //     novelClassesCreated: Number("int"),
 * //   },
 * //   acceptError: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param GetProposalCommandInput - {@link GetProposalCommandInput}
 * @returns {@link GetProposalCommandOutput}
 * @see {@link GetProposalCommandInput} for command's `input` shape.
 * @see {@link GetProposalCommandOutput} for command's `response` shape.
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
 * @example Get a pending proposal with inlined Turtle
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new GetProposalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   metadata: {
 *     columnsProcessed: 84,
 *     datasourceIds: [
 *       "orders_db",
 *       "customers_db"
 *     ],
 *     label: "Sales catalog induction",
 *     novelClassesCreated: 7,
 *     tablesProcessed: 12
 *   },
 *   ontologyId: "ont-sales-2026",
 *   ontologyTurtle: "@prefix : <https://ontology.example.com/sales/> .
 * :Order a owl:Class .",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   r2rmlTurtle: "@prefix rr: <http://www.w3.org/ns/r2rml#> .
 * :OrderMap a rr:TriplesMap .",
 *   status: "pending"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetProposalCommand extends $Command
  .classBuilder<
    GetProposalCommandInput,
    GetProposalCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetProposal", {})
  .n("ControlPlaneServiceClient", "GetProposalCommand")
  .sc(GetProposal$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetProposalInput;
      output: GetProposalOutput;
    };
    sdk: {
      input: GetProposalCommandInput;
      output: GetProposalCommandOutput;
    };
  };
}
