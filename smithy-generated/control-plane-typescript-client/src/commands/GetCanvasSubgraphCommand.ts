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
import type { GetCanvasSubgraphInput, GetCanvasSubgraphOutput } from "../models/models_0";
import { GetCanvasSubgraph$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetCanvasSubgraphCommand}.
 */
export interface GetCanvasSubgraphCommandInput extends GetCanvasSubgraphInput {}
/**
 * @public
 *
 * The output of {@link GetCanvasSubgraphCommand}.
 */
export interface GetCanvasSubgraphCommandOutput extends GetCanvasSubgraphOutput, __MetadataBearer {}

/**
 * One page of canvas nodes and edges, optionally filtered.
 *
 * Unlike the vertex lookup, this does not start from a single IRI: it scans
 * the namespace's named graphs in backend index order and shapes the triples
 * into drawable nodes and edges. Paging is offset-based; pass the previous
 * page's ``nextOffset`` back to continue. ``truncated`` says whether another
 * page exists, so the UI can stop without guessing.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetCanvasSubgraphCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetCanvasSubgraphCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetCanvasSubgraphInput
 *   namespaceId: "STRING_VALUE", // required
 *   kinds: "STRING_VALUE",
 *   graph: "STRING_VALUE",
 *   limit: Number("int"),
 *   offset: Number("int"),
 * };
 * const command = new GetCanvasSubgraphCommand(input);
 * const response = await client.send(command);
 * // { // GetCanvasSubgraphOutput
 * //   nodes: [ // CanvasNodeList // required
 * //     { // CanvasNode
 * //       uri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE",
 * //       kind: "STRING_VALUE",
 * //     },
 * //   ],
 * //   edges: [ // CanvasEdgeList // required
 * //     { // CanvasEdge
 * //       source: "STRING_VALUE", // required
 * //       predicate: "STRING_VALUE", // required
 * //       predicateLabel: "STRING_VALUE",
 * //       target: "STRING_VALUE", // required
 * //       graph: "STRING_VALUE",
 * //       direction: "STRING_VALUE",
 * //     },
 * //   ],
 * //   truncated: true || false, // required
 * //   nodeCount: Number("int"), // required
 * //   edgeCount: Number("int"), // required
 * //   nextOffset: Number("int"),
 * // };
 *
 * ```
 *
 * @param GetCanvasSubgraphCommandInput - {@link GetCanvasSubgraphCommandInput}
 * @returns {@link GetCanvasSubgraphCommandOutput}
 * @see {@link GetCanvasSubgraphCommandInput} for command's `input` shape.
 * @see {@link GetCanvasSubgraphCommandOutput} for command's `response` shape.
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
 * @example List the first page of every kind
 * ```javascript
 * //
 * const input = {
 *   limit: 2,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   offset: 0
 * };
 * const command = new GetCanvasSubgraphCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   edgeCount: 1,
 *   edges: [
 *     {
 *       direction: "outgoing",
 *       graph: "http://coa.amazon.com/onto/sales-crm",
 *       predicate: "http://www.w3.org/2000/01/rdf-schema#subClassOf",
 *       predicateLabel: "subClassOf",
 *       source: "http://example.com/onto#Customer",
 *       target: "http://example.com/onto#Place"
 *     }
 *   ],
 *   nextOffset: 2,
 *   nodeCount: 2,
 *   nodes: [
 *     {
 *       kind: "class",
 *       label: "Customer",
 *       uri: "http://example.com/onto#Customer"
 *     },
 *     {
 *       kind: "class",
 *       label: "Place",
 *       uri: "http://example.com/onto#Place"
 *     }
 *   ],
 *   truncated: true
 * }
 * *\/
 * ```
 *
 * @example Filter one named graph to classes only
 * ```javascript
 * //
 * const input = {
 *   graph: "http://coa.amazon.com/onto/sales-crm",
 *   kinds: "class",
 *   limit: 50,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   offset: 0
 * };
 * const command = new GetCanvasSubgraphCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   edgeCount: 0,
 *   edges:   [],
 *   nodeCount: 1,
 *   nodes: [
 *     {
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
 * @public
 */
export class GetCanvasSubgraphCommand extends $Command
  .classBuilder<
    GetCanvasSubgraphCommandInput,
    GetCanvasSubgraphCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetCanvasSubgraph", {})
  .n("ControlPlaneServiceClient", "GetCanvasSubgraphCommand")
  .sc(GetCanvasSubgraph$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetCanvasSubgraphInput;
      output: GetCanvasSubgraphOutput;
    };
    sdk: {
      input: GetCanvasSubgraphCommandInput;
      output: GetCanvasSubgraphCommandOutput;
    };
  };
}
