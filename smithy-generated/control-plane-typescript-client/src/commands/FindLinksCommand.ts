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
import type { FindLinksInput, FindLinksOutput } from "../models/models_0";
import { FindLinks$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link FindLinksCommand}.
 */
export interface FindLinksCommandInput extends FindLinksInput {}
/**
 * @public
 *
 * The output of {@link FindLinksCommand}.
 */
export interface FindLinksCommandOutput extends FindLinksOutput, __MetadataBearer {}

/**
 * The bounded neighbourhood around one IRI, up to three hops away.
 *
 * Read-only: the graph is never written. Nodes and edges both carry the hop
 * that reached them, so a caller can group by distance and verify the cap.
 * ``maxHops`` above the contractual 3 is rejected by the backend rather than
 * clamped, and a seed with no adjacency returns empty lists — an empty
 * neighbourhood is a valid answer, not an error. When ``limit`` cuts the
 * answer, ``truncated`` says so instead of returning a partial result that
 * looks complete.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, FindLinksCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, FindLinksCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // FindLinksInput
 *   namespaceId: "STRING_VALUE", // required
 *   uri: "STRING_VALUE", // required
 *   direction: "outgoing" || "incoming" || "both",
 *   maxHops: Number("int"),
 *   limit: Number("int"),
 * };
 * const command = new FindLinksCommand(input);
 * const response = await client.send(command);
 * // { // FindLinksOutput
 * //   nodes: [ // GraphLinkNodeList // required
 * //     { // GraphLinkNode
 * //       uri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE",
 * //       kind: "STRING_VALUE",
 * //       hops: Number("int"), // required
 * //     },
 * //   ],
 * //   edges: [ // GraphLinkEdgeList // required
 * //     { // GraphLinkEdge
 * //       source: "STRING_VALUE", // required
 * //       predicate: "STRING_VALUE", // required
 * //       predicateLabel: "STRING_VALUE",
 * //       target: "STRING_VALUE", // required
 * //       graph: "STRING_VALUE",
 * //       direction: "STRING_VALUE",
 * //       hops: Number("int"), // required
 * //     },
 * //   ],
 * //   truncated: true || false, // required
 * // };
 *
 * ```
 *
 * @param FindLinksCommandInput - {@link FindLinksCommandInput}
 * @returns {@link FindLinksCommandOutput}
 * @see {@link FindLinksCommandInput} for command's `input` shape.
 * @see {@link FindLinksCommandOutput} for command's `response` shape.
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
 * @example Two-hop neighbourhood around a class
 * ```javascript
 * //
 * const input = {
 *   direction: "both",
 *   limit: 10,
 *   maxHops: 2,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   uri: "http://example.com/onto#Claim"
 * };
 * const command = new FindLinksCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   edges: [
 *     {
 *       direction: "outgoing",
 *       graph: "https://coa.local/graph/a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d/http%3A%2F%2Fexample.com%2Fonto",
 *       hops: 1,
 *       predicate: "http://www.w3.org/2000/01/rdf-schema#subClassOf",
 *       predicateLabel: "subClassOf",
 *       source: "http://example.com/onto#Claim",
 *       target: "http://example.com/onto#Policy"
 *     },
 *     {
 *       direction: "outgoing",
 *       graph: "https://coa.local/graph/a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d/http%3A%2F%2Fexample.com%2Fonto",
 *       hops: 2,
 *       predicate: "http://example.com/onto#heldBy",
 *       predicateLabel: "heldBy",
 *       source: "http://example.com/onto#Policy",
 *       target: "http://example.com/onto#Customer"
 *     }
 *   ],
 *   nodes: [
 *     {
 *       hops: 1,
 *       kind: "class",
 *       label: "Policy",
 *       uri: "http://example.com/onto#Policy"
 *     },
 *     {
 *       hops: 2,
 *       kind: "class",
 *       label: "Customer",
 *       uri: "http://example.com/onto#Customer"
 *     }
 *   ],
 *   truncated: false
 * }
 * *\/
 * ```
 *
 * @example An IRI with no adjacency is an empty, successful answer
 * ```javascript
 * //
 * const input = {
 *   maxHops: 3,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   uri: "http://example.com/onto#UnusedClass"
 * };
 * const command = new FindLinksCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   edges:   [],
 *   nodes:   [],
 *   truncated: false
 * }
 * *\/
 * ```
 *
 * @public
 */
export class FindLinksCommand extends $Command
  .classBuilder<
    FindLinksCommandInput,
    FindLinksCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "FindLinks", {})
  .n("ControlPlaneServiceClient", "FindLinksCommand")
  .sc(FindLinks$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: FindLinksInput;
      output: FindLinksOutput;
    };
    sdk: {
      input: FindLinksCommandInput;
      output: FindLinksCommandOutput;
    };
  };
}
