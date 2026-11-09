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
import type { ListProposalsInput, ListProposalsOutput } from "../models/models_0";
import { ListProposals$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListProposalsCommand}.
 */
export interface ListProposalsCommandInput extends ListProposalsInput {}
/**
 * @public
 *
 * The output of {@link ListProposalsCommand}.
 */
export interface ListProposalsCommandOutput extends ListProposalsOutput, __MetadataBearer {}

/**
 * List ontology proposals for a namespace, newest first, one page at a time.
 *
 * Proposals are ordered by creation time, newest first, so the first page
 * holds the newest `maxResults` matches and later pages continue with older
 * ones. Keep paging until `nextToken` is absent.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListProposalsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListProposalsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListProposalsInput
 *   namespaceId: "STRING_VALUE", // required
 *   status: "inducing" || "pending" || "accepting" || "embeddings_sync" || "accepted" || "accept_failed" || "rejected" || "cancelled" || "updated" || "failed",
 *   ontologyId: "STRING_VALUE",
 *   sourceType: "STRUCTURED" || "UNSTRUCTURED" || "BRIDGE",
 *   proposalType: "STRING_VALUE",
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListProposalsCommand(input);
 * const response = await client.send(command);
 * // { // ListProposalsOutput
 * //   nextToken: "STRING_VALUE",
 * //   proposals: [ // ProposalSummaryList // required
 * //     { // ProposalSummary
 * //       proposalId: "STRING_VALUE", // required
 * //       status: "inducing" || "pending" || "accepting" || "embeddings_sync" || "accepted" || "accept_failed" || "rejected" || "cancelled" || "updated" || "failed", // required
 * //       ontologyId: "STRING_VALUE", // required
 * //       sourceType: "STRUCTURED" || "UNSTRUCTURED" || "BRIDGE",
 * //       metadata: { // ProposalMetadata
 * //         datasourceIds: [ // DataSourceIdList
 * //           "STRING_VALUE",
 * //         ],
 * //         label: "STRING_VALUE",
 * //         tablesProcessed: Number("int"),
 * //         columnsProcessed: Number("int"),
 * //         novelClassesCreated: Number("int"),
 * //       },
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListProposalsCommandInput - {@link ListProposalsCommandInput}
 * @returns {@link ListProposalsCommandOutput}
 * @see {@link ListProposalsCommandInput} for command's `input` shape.
 * @see {@link ListProposalsCommandOutput} for command's `response` shape.
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
 * @example List pending proposals
 * ```javascript
 * //
 * const input = {
 *   maxResults: 20,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   status: "pending"
 * };
 * const command = new ListProposalsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   nextToken: "eyJvZmZzZXQiOiAyMH0=",
 *   proposals: [
 *     {
 *       metadata: {
 *         columnsProcessed: 84,
 *         datasourceIds: [
 *           "orders_db",
 *           "customers_db"
 *         ],
 *         label: "Sales catalog induction",
 *         novelClassesCreated: 7,
 *         tablesProcessed: 12
 *       },
 *       ontologyId: "ont-sales-2026",
 *       proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *       sourceType: "STRUCTURED",
 *       status: "pending"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListProposalsCommand extends $Command
  .classBuilder<
    ListProposalsCommandInput,
    ListProposalsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListProposals", {})
  .n("ControlPlaneServiceClient", "ListProposalsCommand")
  .sc(ListProposals$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListProposalsInput;
      output: ListProposalsOutput;
    };
    sdk: {
      input: ListProposalsCommandInput;
      output: ListProposalsCommandOutput;
    };
  };
}
