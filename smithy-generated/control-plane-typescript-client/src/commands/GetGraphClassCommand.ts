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
import type { GetGraphClassInput, GraphVertex } from "../models/models_0";
import { GetGraphClass$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetGraphClassCommand}.
 */
export interface GetGraphClassCommandInput extends GetGraphClassInput {}
/**
 * @public
 *
 * The output of {@link GetGraphClassCommand}.
 */
export interface GetGraphClassCommandOutput extends GraphVertex, __MetadataBearer {}

/**
 * Look up a class vertex by IRI.
 *
 * The IRI is passed as a query parameter (``?uri=…``) rather than a
 * path label to avoid double-encoding issues with slashes and hash
 * fragments common in OWL IRIs (e.g. ``http://example.org/ont#Foo``).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetGraphClassCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetGraphClassCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetGraphClassInput
 *   namespaceId: "STRING_VALUE", // required
 *   uri: "STRING_VALUE", // required
 * };
 * const command = new GetGraphClassCommand(input);
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
 * @param GetGraphClassCommandInput - {@link GetGraphClassCommandInput}
 * @returns {@link GetGraphClassCommandOutput}
 * @see {@link GetGraphClassCommandInput} for command's `input` shape.
 * @see {@link GetGraphClassCommandOutput} for command's `response` shape.
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
 * @example Look up a class vertex by IRI
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   uri: "http://example.com/onto#Customer"
 * };
 * const command = new GetGraphClassCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   altLabels: [
 *     "Client",
 *     "Account"
 *   ],
 *   comments: [
 *     "A party that purchases goods or services."
 *   ],
 *   edges: [
 *     {
 *       direction: "outbound",
 *       neighbor: {
 *         kind: "class",
 *         label: "Order",
 *         uri: "http://example.com/onto#Order"
 *       },
 *       predicate: "http://example.com/onto#placedOrder",
 *       predicateLabel: "placed order"
 *     }
 *   ],
 *   graphUris: [
 *     "http://coa.amazon.com/onto/sales-crm"
 *   ],
 *   isMapped: true,
 *   kind: "class",
 *   labels: [
 *     "Customer"
 *   ],
 *   namespace: "sales-analytics",
 *   types: [
 *     "http://www.w3.org/2002/07/owl#Class"
 *   ],
 *   uri: "http://example.com/onto#Customer"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetGraphClassCommand extends $Command
  .classBuilder<
    GetGraphClassCommandInput,
    GetGraphClassCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetGraphClass", {})
  .n("ControlPlaneServiceClient", "GetGraphClassCommand")
  .sc(GetGraphClass$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetGraphClassInput;
      output: GraphVertex;
    };
    sdk: {
      input: GetGraphClassCommandInput;
      output: GetGraphClassCommandOutput;
    };
  };
}
