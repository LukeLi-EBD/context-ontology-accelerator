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
import type { GetGraphDatatypePropertyInput, GraphVertex } from "../models/models_0";
import { GetGraphDatatypeProperty$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetGraphDatatypePropertyCommand}.
 */
export interface GetGraphDatatypePropertyCommandInput extends GetGraphDatatypePropertyInput {}
/**
 * @public
 *
 * The output of {@link GetGraphDatatypePropertyCommand}.
 */
export interface GetGraphDatatypePropertyCommandOutput extends GraphVertex, __MetadataBearer {}

/**
 * Look up a datatype-property vertex by IRI (query param).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetGraphDatatypePropertyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetGraphDatatypePropertyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetGraphDatatypePropertyInput
 *   namespaceId: "STRING_VALUE", // required
 *   uri: "STRING_VALUE", // required
 * };
 * const command = new GetGraphDatatypePropertyCommand(input);
 * const response = await client.send(command);
 * // { // GraphVertex
 * //   uri: "STRING_VALUE", // required
 * //   kind: "STRING_VALUE", // required
 * //   namespace: "STRING_VALUE", // required
 * //   types: [ // StringList
 * //     "STRING_VALUE",
 * //   ],
 * //   labels: [
 * //     "STRING_VALUE",
 * //   ],
 * //   comments: [
 * //     "STRING_VALUE",
 * //   ],
 * //   altLabels: [
 * //     "STRING_VALUE",
 * //   ],
 * //   graphUris: [
 * //     "STRING_VALUE",
 * //   ],
 * //   isMapped: true || false,
 * //   superseded: { // SupersededAnnotations
 * //     "<keys>": "<StringList>",
 * //   },
 * //   edges: [ // GraphEdgeList
 * //     { // GraphEdge
 * //       predicate: "STRING_VALUE", // required
 * //       predicateLabel: "STRING_VALUE",
 * //       direction: "STRING_VALUE", // required
 * //       neighbor: { // GraphNeighbor
 * //         uri: "STRING_VALUE", // required
 * //         label: "STRING_VALUE",
 * //         kind: "STRING_VALUE", // required
 * //       },
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param GetGraphDatatypePropertyCommandInput - {@link GetGraphDatatypePropertyCommandInput}
 * @returns {@link GetGraphDatatypePropertyCommandOutput}
 * @see {@link GetGraphDatatypePropertyCommandInput} for command's `input` shape.
 * @see {@link GetGraphDatatypePropertyCommandOutput} for command's `response` shape.
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
 * @example Look up a datatype-property vertex by IRI
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   uri: "http://example.com/onto#emailAddress"
 * };
 * const command = new GetGraphDatatypePropertyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   edges: [
 *     {
 *       direction: "outbound",
 *       neighbor: {
 *         kind: "literal",
 *         uri: "http://www.w3.org/2001/XMLSchema#string"
 *       },
 *       predicate: "http://www.w3.org/2000/01/rdf-schema#range"
 *     }
 *   ],
 *   graphUris: [
 *     "http://coa.amazon.com/onto/sales-crm"
 *   ],
 *   kind: "datatype-property",
 *   labels: [
 *     "email address"
 *   ],
 *   namespace: "sales-analytics",
 *   types: [
 *     "http://www.w3.org/2002/07/owl#DatatypeProperty"
 *   ],
 *   uri: "http://example.com/onto#emailAddress"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetGraphDatatypePropertyCommand extends $Command
  .classBuilder<
    GetGraphDatatypePropertyCommandInput,
    GetGraphDatatypePropertyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetGraphDatatypeProperty", {})
  .n("ControlPlaneServiceClient", "GetGraphDatatypePropertyCommand")
  .sc(GetGraphDatatypeProperty$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetGraphDatatypePropertyInput;
      output: GraphVertex;
    };
    sdk: {
      input: GetGraphDatatypePropertyCommandInput;
      output: GetGraphDatatypePropertyCommandOutput;
    };
  };
}
