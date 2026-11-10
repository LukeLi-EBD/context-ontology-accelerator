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
import type { FindGraphPathInput, FindGraphPathOutput } from "../models/models_0";
import { FindGraphPath$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link FindGraphPathCommand}.
 */
export interface FindGraphPathCommandInput extends FindGraphPathInput {}
/**
 * @public
 *
 * The output of {@link FindGraphPathCommand}.
 */
export interface FindGraphPathCommandOutput extends FindGraphPathOutput, __MetadataBearer {}

/**
 * Find simple paths between two IRIs, up to a bounded hop count.
 *
 * Read-only: the graph is never written. ``maxHops`` and ``limit`` are
 * clamped by the backend's published canvas limits; when the enumeration
 * hits the cap, ``truncated`` says so rather than silently returning a
 * partial answer as if it were complete.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, FindGraphPathCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, FindGraphPathCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // FindGraphPathInput
 *   namespaceId: "STRING_VALUE", // required
 *   start: "STRING_VALUE", // required
 *   end: "STRING_VALUE", // required
 *   maxHops: Number("int"),
 *   limit: Number("int"),
 * };
 * const command = new FindGraphPathCommand(input);
 * const response = await client.send(command);
 * // { // FindGraphPathOutput
 * //   paths: [ // GraphPathList // required
 * //     { // GraphPath
 * //       nodes: [ // CanvasNodeList // required
 * //         { // CanvasNode
 * //           uri: "STRING_VALUE", // required
 * //           label: "STRING_VALUE",
 * //           kind: "STRING_VALUE",
 * //         },
 * //       ],
 * //       edges: [ // CanvasEdgeList // required
 * //         { // CanvasEdge
 * //           source: "STRING_VALUE", // required
 * //           predicate: "STRING_VALUE", // required
 * //           predicateLabel: "STRING_VALUE",
 * //           target: "STRING_VALUE", // required
 * //           graph: "STRING_VALUE",
 * //           direction: "STRING_VALUE",
 * //         },
 * //       ],
 * //       hops: Number("int"), // required
 * //     },
 * //   ],
 * //   truncated: true || false, // required
 * // };
 *
 * ```
 *
 * @param FindGraphPathCommandInput - {@link FindGraphPathCommandInput}
 * @returns {@link FindGraphPathCommandOutput}
 * @see {@link FindGraphPathCommandInput} for command's `input` shape.
 * @see {@link FindGraphPathCommandOutput} for command's `response` shape.
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
 * @example Find paths from a customer to a place
 * ```javascript
 * //
 * const input = {
 *   end: "http://example.com/onto#Place",
 *   limit: 5,
 *   maxHops: 3,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   start: "http://example.com/onto#Customer"
 * };
 * const command = new FindGraphPathCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   paths: [
 *     {
 *       edges: [
 *         {
 *           direction: "outgoing",
 *           graph: "http://coa.amazon.com/onto/sales-crm",
 *           predicate: "http://www.w3.org/2000/01/rdf-schema#subClassOf",
 *           predicateLabel: "subClassOf",
 *           source: "http://example.com/onto#Customer",
 *           target: "http://example.com/onto#Place"
 *         }
 *       ],
 *       hops: 1,
 *       nodes: [
 *         {
 *           kind: "class",
 *           label: "Customer",
 *           uri: "http://example.com/onto#Customer"
 *         },
 *         {
 *           kind: "class",
 *           label: "Place",
 *           uri: "http://example.com/onto#Place"
 *         }
 *       ]
 *     }
 *   ],
 *   truncated: false
 * }
 * *\/
 * ```
 *
 * @public
 */
export class FindGraphPathCommand extends $Command
  .classBuilder<
    FindGraphPathCommandInput,
    FindGraphPathCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "FindGraphPath", {})
  .n("ControlPlaneServiceClient", "FindGraphPathCommand")
  .sc(FindGraphPath$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: FindGraphPathInput;
      output: FindGraphPathOutput;
    };
    sdk: {
      input: FindGraphPathCommandInput;
      output: FindGraphPathCommandOutput;
    };
  };
}
