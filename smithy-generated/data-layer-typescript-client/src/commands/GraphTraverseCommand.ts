// smithy-typescript generated code
import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { Command as $Command } from "@smithy/smithy-client";
import type { MetadataBearer as __MetadataBearer } from "@smithy/types";

import type {
  DataLayerServiceClientResolvedConfig,
  ServiceInputTypes,
  ServiceOutputTypes,
} from "../DataLayerServiceClient";
import { commonParams } from "../endpoint/EndpointParameters";
import type { GraphTraverseInput, GraphTraverseOutput } from "../models/models_0";
import { GraphTraverse$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GraphTraverseCommand}.
 */
export interface GraphTraverseCommandInput extends GraphTraverseInput {}
/**
 * @public
 *
 * The output of {@link GraphTraverseCommand}.
 */
export interface GraphTraverseCommandOutput extends GraphTraverseOutput, __MetadataBearer {}

/**
 * Traverse the knowledge graph outward from a starting entity URI, following
 * relationships up to a maximum depth in the requested direction.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { DataLayerServiceClient, GraphTraverseCommand } from "@coa/data-layer-client"; // ES Modules import
 * // const { DataLayerServiceClient, GraphTraverseCommand } = require("@coa/data-layer-client"); // CommonJS import
 * // import type { DataLayerServiceClientConfig } from "@coa/data-layer-client";
 * const config = {}; // type is DataLayerServiceClientConfig
 * const client = new DataLayerServiceClient(config);
 * const input = { // GraphTraverseInput
 *   namespaceId: "STRING_VALUE", // required
 *   startUri: "STRING_VALUE", // required
 *   maxDepth: Number("int"),
 *   relationshipFilter: [ // FilterValueList
 *     "STRING_VALUE",
 *   ],
 *   direction: "outgoing" || "incoming" || "both",
 *   maxResults: Number("int"),
 * };
 * const command = new GraphTraverseCommand(input);
 * const response = await client.send(command);
 * // { // GraphTraverseOutput
 * //   entities: [ // EntityList // required
 * //     { // Entity
 * //       uri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       type: "STRING_VALUE",
 * //       properties: { // PropertyMap
 * //         "<keys>": "STRING_VALUE",
 * //       },
 * //     },
 * //   ],
 * //   relationships: [ // RelationshipList // required
 * //     { // Relationship
 * //       sourceUri: "STRING_VALUE", // required
 * //       predicateUri: "STRING_VALUE", // required
 * //       targetUri: "STRING_VALUE", // required
 * //       predicateLabel: "STRING_VALUE",
 * //     },
 * //   ],
 * //   trace: [ // TraceStepList // required
 * //     { // TraceStep
 * //       step: "STRING_VALUE", // required
 * //       status: "STRING_VALUE", // required
 * //       durationMs: Number("long"),
 * //       detail: "STRING_VALUE",
 * //       toolUsed: "STRING_VALUE",
 * //       parallelGroup: "STRING_VALUE",
 * //       wallMs: Number("long"),
 * //       conformanceWarnings: [ // ConformanceWarningList
 * //         { // ConformanceWarning
 * //           row: Number("int"), // required
 * //           shape: "STRING_VALUE", // required
 * //           message: "STRING_VALUE", // required
 * //         },
 * //       ],
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param GraphTraverseCommandInput - {@link GraphTraverseCommandInput}
 * @returns {@link GraphTraverseCommandOutput}
 * @see {@link GraphTraverseCommandInput} for command's `input` shape.
 * @see {@link GraphTraverseCommandOutput} for command's `response` shape.
 * @see {@link DataLayerServiceClientResolvedConfig | config} for DataLayerServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link NamespaceNotFoundError} (client fault)
 *  Returned with HTTP 404 when the target namespace does not exist or is not
 * visible to the caller.
 *
 * @throws {@link OntologyNotPublishedError} (client fault)
 *  Returned with HTTP 409 when the namespace has no published ontology, so the
 * query cannot be resolved against a schema yet.
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
 *
 * @throws {@link RateLimitExceededError} (client fault)
 *  Returned with HTTP 429 when the caller exceeds the request rate limit;
 * `retryAfterSeconds` indicates how long to wait before retrying.
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
 * @throws {@link DataLayerServiceServiceException}
 * <p>Base exception class for all service exceptions from DataLayerService service.</p>
 *
 *
 * @example Traverse from an entity
 * ```javascript
 * //
 * const input = {
 *   direction: "outgoing",
 *   maxDepth: 2,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   startUri: "urn:coa:customer:acme-corp"
 * };
 * const command = new GraphTraverseCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   entities: [
 *     {
 *       label: "Acme Corp",
 *       type: "Customer",
 *       uri: "urn:coa:customer:acme-corp"
 *     },
 *     {
 *       label: "Order 1001",
 *       type: "Order",
 *       uri: "urn:coa:order:o-1001"
 *     }
 *   ],
 *   relationships: [
 *     {
 *       predicateLabel: "placed",
 *       predicateUri: "urn:coa:rel:placed",
 *       sourceUri: "urn:coa:customer:acme-corp",
 *       targetUri: "urn:coa:order:o-1001"
 *     }
 *   ],
 *   trace: [
 *     {
 *       durationMs: 66,
 *       status: "ok",
 *       step: "graph-traverse"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GraphTraverseCommand extends $Command
  .classBuilder<
    GraphTraverseCommandInput,
    GraphTraverseCommandOutput,
    DataLayerServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: DataLayerServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("DataLayerService", "GraphTraverse", {})
  .n("DataLayerServiceClient", "GraphTraverseCommand")
  .sc(GraphTraverse$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GraphTraverseInput;
      output: GraphTraverseOutput;
    };
    sdk: {
      input: GraphTraverseCommandInput;
      output: GraphTraverseCommandOutput;
    };
  };
}
