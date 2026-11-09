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
import type { EmbeddingListOutput, GetEntityEmbeddingsInput } from "../models/models_0";
import { GetEntityEmbeddings$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetEntityEmbeddingsCommand}.
 */
export interface GetEntityEmbeddingsCommandInput extends GetEntityEmbeddingsInput {}
/**
 * @public
 *
 * The output of {@link GetEntityEmbeddingsCommand}.
 */
export interface GetEntityEmbeddingsCommandOutput extends EmbeddingListOutput, __MetadataBearer {}

/**
 * Return every stored embedding (vector included) for one entity URI.
 *
 * Chunk vectors are addressed as `urn:coa:chunk:<chunkId>`; filtering by
 * `entityType: "chunk"` and `embeddingType: "chunk"` narrows the scan.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetEntityEmbeddingsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetEntityEmbeddingsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetEntityEmbeddingsInput
 *   namespaceId: "STRING_VALUE", // required
 *   entityUri: "STRING_VALUE", // required
 *   entityType: "STRING_VALUE",
 *   embeddingType: "STRING_VALUE",
 *   modelId: "STRING_VALUE",
 * };
 * const command = new GetEntityEmbeddingsCommand(input);
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
 * @param GetEntityEmbeddingsCommandInput - {@link GetEntityEmbeddingsCommandInput}
 * @returns {@link GetEntityEmbeddingsCommandOutput}
 * @see {@link GetEntityEmbeddingsCommandInput} for command's `input` shape.
 * @see {@link GetEntityEmbeddingsCommandOutput} for command's `response` shape.
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
 * @example Read a chunk's vector
 * ```javascript
 * //
 * const input = {
 *   embeddingType: "chunk",
 *   entityType: "chunk",
 *   entityUri: "urn:coa:chunk:1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new GetEntityEmbeddingsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   embeddings: [
 *     {
 *       createdAt: "2026-11-10T08:00:00Z",
 *       dimensions: 1024,
 *       embeddingType: "chunk",
 *       entityType: "chunk",
 *       entityUri: "urn:coa:chunk:1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
 *       id: "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
 *       modelId: "BAAI/bge-m3",
 *       ontologyId: "urn:coa:abox:documents",
 *       vector: [
 *         0.1,
 *         0.2,
 *         0.3
 *       ]
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetEntityEmbeddingsCommand extends $Command
  .classBuilder<
    GetEntityEmbeddingsCommandInput,
    GetEntityEmbeddingsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetEntityEmbeddings", {})
  .n("ControlPlaneServiceClient", "GetEntityEmbeddingsCommand")
  .sc(GetEntityEmbeddings$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetEntityEmbeddingsInput;
      output: EmbeddingListOutput;
    };
    sdk: {
      input: GetEntityEmbeddingsCommandInput;
      output: GetEntityEmbeddingsCommandOutput;
    };
  };
}
