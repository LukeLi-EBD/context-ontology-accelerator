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
import type { QueryInput, QueryOutput } from "../models/models_0";
import { Query$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link QueryCommand}.
 */
export interface QueryCommandInput extends QueryInput {}
/**
 * @public
 *
 * The output of {@link QueryCommand}.
 */
export interface QueryCommandOutput extends QueryOutput, __MetadataBearer {}

/**
 * Answer a natural-language question against the namespace. Routes through the
 * tiered resolver (metric match → structured query → knowledge-base retrieval)
 * and returns a typed result with confidence and an execution trace.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { DataLayerServiceClient, QueryCommand } from "@coa/data-layer-client"; // ES Modules import
 * // const { DataLayerServiceClient, QueryCommand } = require("@coa/data-layer-client"); // CommonJS import
 * // import type { DataLayerServiceClientConfig } from "@coa/data-layer-client";
 * const config = {}; // type is DataLayerServiceClientConfig
 * const client = new DataLayerServiceClient(config);
 * const input = { // QueryInput
 *   namespaceId: "STRING_VALUE", // required
 *   query: "STRING_VALUE", // required
 *   execute: true || false,
 *   tierOverride: Number("int"),
 *   mode: "standard" || "deep-reasoning" || "agentic",
 *   strategy: "best" || "ontop" || "nl_to_sql" || "ontop_first" || "nl_to_sql_first" || "deep-reasoning" || "nl_to_sparql",
 *   dimensions: [ // DimensionFilterList
 *     { // DimensionFilter
 *       name: "STRING_VALUE", // required
 *       value: "STRING_VALUE", // required
 *       operator: "=",
 *     },
 *   ],
 *   timeoutMs: Number("long"),
 *   includeSupporting: true || false,
 *   includeDebugInfo: true || false,
 *   maxResults: Number("int"),
 * };
 * const command = new QueryCommand(input);
 * const response = await client.send(command);
 * // { // QueryOutput
 * //   result: { // QueryResult
 * //     tier: Number("int"), // required
 * //     confidence: { // ConfidenceScore
 * //       score: Number("float"), // required
 * //       rationale: "STRING_VALUE",
 * //     },
 * //     resultRows: [ // ResultRowList
 * //       { // ResultRow
 * //         "<keys>": "STRING_VALUE",
 * //       },
 * //     ],
 * //     synthesizedAnswer: "STRING_VALUE",
 * //     queryUsed: "STRING_VALUE",
 * //     sparqlGenerated: "STRING_VALUE",
 * //     supportingContent: [ // SupportingContentList
 * //       { // SupportingContent
 * //         chunkId: "STRING_VALUE", // required
 * //         text: "STRING_VALUE", // required
 * //         sourceDocumentId: "STRING_VALUE",
 * //         sourceDocumentName: "STRING_VALUE",
 * //         relevanceScore: Number("float"),
 * //         entityAnnotations: [ // StringList
 * //           "STRING_VALUE",
 * //         ],
 * //       },
 * //     ],
 * //     graphContext: { // GraphContext
 * //       entities: [ // EntityList
 * //         { // Entity
 * //           uri: "STRING_VALUE", // required
 * //           label: "STRING_VALUE", // required
 * //           type: "STRING_VALUE",
 * //           properties: { // PropertyMap
 * //             "<keys>": "STRING_VALUE",
 * //           },
 * //         },
 * //       ],
 * //       relationships: [ // RelationshipList
 * //         { // Relationship
 * //           sourceUri: "STRING_VALUE", // required
 * //           predicateUri: "STRING_VALUE", // required
 * //           targetUri: "STRING_VALUE", // required
 * //           predicateLabel: "STRING_VALUE",
 * //         },
 * //       ],
 * //     },
 * //     trace: [ // TraceStepList // required
 * //       { // TraceStep
 * //         step: "STRING_VALUE", // required
 * //         status: "STRING_VALUE", // required
 * //         durationMs: Number("long"),
 * //         detail: "STRING_VALUE",
 * //         toolUsed: "STRING_VALUE",
 * //         parallelGroup: "STRING_VALUE",
 * //         wallMs: Number("long"),
 * //         conformanceWarnings: [ // ConformanceWarningList
 * //           { // ConformanceWarning
 * //             row: Number("int"), // required
 * //             shape: "STRING_VALUE", // required
 * //             message: "STRING_VALUE", // required
 * //           },
 * //         ],
 * //       },
 * //     ],
 * //     ontologyVersion: "STRING_VALUE",
 * //     dataSources: [
 * //       "STRING_VALUE",
 * //     ],
 * //     partial: true || false,
 * //     executionMode: "STRING_VALUE",
 * //   },
 * //   requestId: "STRING_VALUE",
 * //   sessionId: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param QueryCommandInput - {@link QueryCommandInput}
 * @returns {@link QueryCommandOutput}
 * @see {@link QueryCommandInput} for command's `input` shape.
 * @see {@link QueryCommandOutput} for command's `response` shape.
 * @see {@link DataLayerServiceClientResolvedConfig | config} for DataLayerServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
 *
 * @throws {@link NamespaceNotFoundError} (client fault)
 *  Returned with HTTP 404 when the target namespace does not exist or is not
 * visible to the caller.
 *
 * @throws {@link NoResultError} (client fault)
 *  Returned with HTTP 404 when a pinned tier produced no data for the query —
 * a "no results" outcome rather than a server error.
 *
 * @throws {@link OntologyNotPublishedError} (client fault)
 *  Returned with HTTP 409 when the namespace has no published ontology, so the
 * query cannot be resolved against a schema yet.
 *
 * @throws {@link QueryTranslationError} (client fault)
 *  Returned with HTTP 400 when a natural-language question cannot be translated
 * into an executable query against the ontology.
 *
 * @throws {@link VKGExecutionError} (server fault)
 *  Returned with HTTP 502 when the virtual knowledge graph fails to execute the
 * generated SPARQL query.
 *
 * Carries a fixed, client-safe message only. The failing query and the
 * backend's own error text are deliberately not returned: they name internal
 * schema objects and endpoints. Operators correlate a failure through the
 * request id instead.
 *
 * @throws {@link DataSourceUnavailableError} (server fault)
 *  Returned with HTTP 502 when a backing data source cannot be reached to
 * answer the query; `dataSourceId` identifies the unavailable source.
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
 * @example Ask a natural-language question
 * ```javascript
 * //
 * const input = {
 *   execute: true,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   query: "What was total revenue in Q3 2025?"
 * };
 * const command = new QueryCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   requestId: "req-01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *   result: {
 *     confidence: {
 *       rationale: "Exact metric match on 'total revenue'",
 *       score: 0.94
 *     },
 *     resultRows: [
 *       {
 *         period: "Q3 2025",
 *         revenue: "12450000"
 *       }
 *     ],
 *     synthesizedAnswer: "Total revenue in Q3 2025 was $12.45M.",
 *     tier: 1,
 *     trace: [
 *       {
 *         durationMs: 42,
 *         status: "ok",
 *         step: "metric-match"
 *       }
 *     ]
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class QueryCommand extends $Command
  .classBuilder<
    QueryCommandInput,
    QueryCommandOutput,
    DataLayerServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: DataLayerServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("DataLayerService", "Query", {})
  .n("DataLayerServiceClient", "QueryCommand")
  .sc(Query$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: QueryInput;
      output: QueryOutput;
    };
    sdk: {
      input: QueryCommandInput;
      output: QueryCommandOutput;
    };
  };
}
