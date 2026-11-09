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
import type { KBSearchInput, KBSearchOutput } from "../models/models_0";
import { KBSearch$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link KBSearchCommand}.
 */
export interface KBSearchCommandInput extends KBSearchInput {}
/**
 * @public
 *
 * The output of {@link KBSearchCommand}.
 */
export interface KBSearchCommandOutput extends KBSearchOutput, __MetadataBearer {}

/**
 * Semantic search over the namespace's document knowledge base, returning
 * ranked supporting chunks with their source provenance.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { DataLayerServiceClient, KBSearchCommand } from "@coa/data-layer-client"; // ES Modules import
 * // const { DataLayerServiceClient, KBSearchCommand } = require("@coa/data-layer-client"); // CommonJS import
 * // import type { DataLayerServiceClientConfig } from "@coa/data-layer-client";
 * const config = {}; // type is DataLayerServiceClientConfig
 * const client = new DataLayerServiceClient(config);
 * const input = { // KBSearchInput
 *   namespaceId: "STRING_VALUE", // required
 *   query: "STRING_VALUE", // required
 *   topK: Number("int"),
 *   minScore: Number("float"),
 *   sourceFilter: [ // FilterValueList
 *     "STRING_VALUE",
 *   ],
 *   entityFilter: [
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new KBSearchCommand(input);
 * const response = await client.send(command);
 * // { // KBSearchOutput
 * //   chunks: [ // SupportingContentList // required
 * //     { // SupportingContent
 * //       chunkId: "STRING_VALUE", // required
 * //       text: "STRING_VALUE", // required
 * //       sourceDocumentId: "STRING_VALUE",
 * //       sourceDocumentName: "STRING_VALUE",
 * //       relevanceScore: Number("float"),
 * //       entityAnnotations: [ // StringList
 * //         "STRING_VALUE",
 * //       ],
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
 * //   queryEmbeddingModel: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param KBSearchCommandInput - {@link KBSearchCommandInput}
 * @returns {@link KBSearchCommandOutput}
 * @see {@link KBSearchCommandInput} for command's `input` shape.
 * @see {@link KBSearchCommandOutput} for command's `response` shape.
 * @see {@link DataLayerServiceClientResolvedConfig | config} for DataLayerServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link NamespaceNotFoundError} (client fault)
 *  Returned with HTTP 404 when the target namespace does not exist or is not
 * visible to the caller.
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
 * @example Search the knowledge base
 * ```javascript
 * //
 * const input = {
 *   minScore: 0.5,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   query: "refund policy for enterprise contracts",
 *   topK: 3
 * };
 * const command = new KBSearchCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   chunks: [
 *     {
 *       chunkId: "doc-42#p7",
 *       relevanceScore: 0.82,
 *       sourceDocumentId: "src-6f8b4f12",
 *       sourceDocumentName: "Enterprise Terms.pdf",
 *       text: "Enterprise contracts allow refunds within 30 days of invoice."
 *     }
 *   ],
 *   queryEmbeddingModel: "amazon.titan-embed-text-v2",
 *   trace: [
 *     {
 *       durationMs: 128,
 *       status: "ok",
 *       step: "kb-search"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class KBSearchCommand extends $Command
  .classBuilder<
    KBSearchCommandInput,
    KBSearchCommandOutput,
    DataLayerServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: DataLayerServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("DataLayerService", "KBSearch", {})
  .n("DataLayerServiceClient", "KBSearchCommand")
  .sc(KBSearch$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: KBSearchInput;
      output: KBSearchOutput;
    };
    sdk: {
      input: KBSearchCommandInput;
      output: KBSearchCommandOutput;
    };
  };
}
