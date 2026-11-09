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
import type { GraphSearchInput, GraphSearchOutput } from "../models/models_0";
import { GraphSearch$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GraphSearchCommand}.
 */
export interface GraphSearchCommandInput extends GraphSearchInput {}
/**
 * @public
 *
 * The output of {@link GraphSearchCommand}.
 */
export interface GraphSearchCommandOutput extends GraphSearchOutput, __MetadataBearer {}

/**
 * Substring search over entity IRIs and labels in a namespace's graphs.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GraphSearchCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GraphSearchCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GraphSearchInput
 *   namespaceId: "STRING_VALUE", // required
 *   q: "STRING_VALUE", // required
 *   kind: "class" || "object-property" || "datatype-property" || "annotation-property" || "ontology" || "property" || "literal" || "blank-node" || "unknown",
 *   ontologyId: "STRING_VALUE",
 *   excludeOntologyId: "STRING_VALUE",
 *   limit: Number("int"),
 *   offset: Number("int"),
 * };
 * const command = new GraphSearchCommand(input);
 * const response = await client.send(command);
 * // { // GraphSearchOutput
 * //   hits: [ // GraphSearchHitList // required
 * //     { // GraphSearchHit
 * //       uri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE",
 * //       kind: "STRING_VALUE", // required
 * //       graphUris: [ // StringList
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   ],
 * //   totalCount: Number("int"),
 * // };
 *
 * ```
 *
 * @param GraphSearchCommandInput - {@link GraphSearchCommandInput}
 * @returns {@link GraphSearchCommandOutput}
 * @see {@link GraphSearchCommandInput} for command's `input` shape.
 * @see {@link GraphSearchCommandOutput} for command's `response` shape.
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
 * @example Search for class vertices matching a term
 * ```javascript
 * //
 * const input = {
 *   kind: "class",
 *   limit: 10,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   offset: 0,
 *   q: "customer"
 * };
 * const command = new GraphSearchCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   hits: [
 *     {
 *       graphUris: [
 *         "http://coa.amazon.com/onto/sales-crm"
 *       ],
 *       kind: "class",
 *       label: "Customer",
 *       uri: "http://example.com/onto#Customer"
 *     }
 *   ],
 *   totalCount: 1
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GraphSearchCommand extends $Command
  .classBuilder<
    GraphSearchCommandInput,
    GraphSearchCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GraphSearch", {})
  .n("ControlPlaneServiceClient", "GraphSearchCommand")
  .sc(GraphSearch$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GraphSearchInput;
      output: GraphSearchOutput;
    };
    sdk: {
      input: GraphSearchCommandInput;
      output: GraphSearchCommandOutput;
    };
  };
}
