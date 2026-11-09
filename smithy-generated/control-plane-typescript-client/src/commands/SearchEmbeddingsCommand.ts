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
import type { EmbeddingListOutput, SearchEmbeddingsInput } from "../models/models_0";
import { SearchEmbeddings$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link SearchEmbeddingsCommand}.
 */
export interface SearchEmbeddingsCommandInput extends SearchEmbeddingsInput {}
/**
 * @public
 *
 * The output of {@link SearchEmbeddingsCommand}.
 */
export interface SearchEmbeddingsCommandOutput extends EmbeddingListOutput, __MetadataBearer {}

/**
 * k-nearest-neighbour search over a namespace's stored vectors.
 *
 * The caller supplies the query vector (the web app reuses the vector already
 * stored for a chunk); no embedding is computed server-side.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, SearchEmbeddingsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, SearchEmbeddingsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // SearchEmbeddingsInput
 *   namespaceId: "STRING_VALUE", // required
 *   vector: [ // DoubleList // required
 *     Number("double"),
 *   ],
 *   embeddingType: "STRING_VALUE", // required
 *   modelId: "STRING_VALUE", // required
 *   entityType: "STRING_VALUE",
 *   ontologyId: "STRING_VALUE",
 *   topK: Number("int"),
 * };
 * const command = new SearchEmbeddingsCommand(input);
 * const response = await client.send(command);
 * // { // EmbeddingListOutput
 * //   embeddings: [ // EmbeddingRecordList // required
 * //     { // EmbeddingRecord
 * //       id: "STRING_VALUE", // required
 * //       ontologyId: "STRING_VALUE", // required
 * //       entityUri: "STRING_VALUE", // required
 * //       entityType: "STRING_VALUE", // required
 * //       embeddingType: "STRING_VALUE", // required
 * //       modelId: "STRING_VALUE", // required
 * //       dimensions: Number("int"), // required
 * //       text: "STRING_VALUE",
 * //       createdAt: "STRING_VALUE",
 * //       metadata: "DOCUMENT_VALUE",
 * //       vector: [ // DoubleList // required
 * //         Number("double"),
 * //       ],
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param SearchEmbeddingsCommandInput - {@link SearchEmbeddingsCommandInput}
 * @returns {@link SearchEmbeddingsCommandOutput}
 * @see {@link SearchEmbeddingsCommandInput} for command's `input` shape.
 * @see {@link SearchEmbeddingsCommandOutput} for command's `response` shape.
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
 * @example Search the five nearest chunk vectors
 * ```javascript
 * //
 * const input = {
 *   embeddingType: "chunk",
 *   entityType: "chunk",
 *   modelId: "BAAI/bge-m3",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   topK: 5,
 *   vector: [
 *     0.1,
 *     0.2,
 *     0.3
 *   ]
 * };
 * const command = new SearchEmbeddingsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   embeddings:   []
 * }
 * *\/
 * ```
 *
 * @public
 */
export class SearchEmbeddingsCommand extends $Command
  .classBuilder<
    SearchEmbeddingsCommandInput,
    SearchEmbeddingsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "SearchEmbeddings", {})
  .n("ControlPlaneServiceClient", "SearchEmbeddingsCommand")
  .sc(SearchEmbeddings$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: SearchEmbeddingsInput;
      output: EmbeddingListOutput;
    };
    sdk: {
      input: SearchEmbeddingsCommandInput;
      output: SearchEmbeddingsCommandOutput;
    };
  };
}
