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
import type { ListDocumentChunksInput, ListDocumentChunksOutput } from "../models/models_0";
import { ListDocumentChunks$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListDocumentChunksCommand}.
 */
export interface ListDocumentChunksCommandInput extends ListDocumentChunksInput {}
/**
 * @public
 *
 * The output of {@link ListDocumentChunksCommand}.
 */
export interface ListDocumentChunksCommandOutput extends ListDocumentChunksOutput, __MetadataBearer {}

/**
 * List the chunks of one document in document order.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListDocumentChunksCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListDocumentChunksCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListDocumentChunksInput
 *   namespaceId: "STRING_VALUE", // required
 *   documentId: "STRING_VALUE", // required
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListDocumentChunksCommand(input);
 * const response = await client.send(command);
 * // { // ListDocumentChunksOutput
 * //   nextToken: "STRING_VALUE",
 * //   items: [ // DocumentChunkList // required
 * //     { // DocumentChunk
 * //       chunkId: "STRING_VALUE", // required
 * //       page: Number("int"), // required
 * //       text: "STRING_VALUE", // required
 * //       charStart: Number("int"), // required
 * //       charEnd: Number("int"), // required
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListDocumentChunksCommandInput - {@link ListDocumentChunksCommandInput}
 * @returns {@link ListDocumentChunksCommandOutput}
 * @see {@link ListDocumentChunksCommandInput} for command's `input` shape.
 * @see {@link ListDocumentChunksCommandOutput} for command's `response` shape.
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
 * @example List one document's chunks
 * ```javascript
 * //
 * const input = {
 *   documentId: "9a7b6c5d-4e3f-4a2b-8c1d-0e9f8a7b6c5d",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new ListDocumentChunksCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   items: [
 *     {
 *       charEnd: 6,
 *       charStart: 0,
 *       chunkId: "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
 *       page: 1,
 *       text: "示例切片文本"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListDocumentChunksCommand extends $Command
  .classBuilder<
    ListDocumentChunksCommandInput,
    ListDocumentChunksCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListDocumentChunks", {})
  .n("ControlPlaneServiceClient", "ListDocumentChunksCommand")
  .sc(ListDocumentChunks$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListDocumentChunksInput;
      output: ListDocumentChunksOutput;
    };
    sdk: {
      input: ListDocumentChunksCommandInput;
      output: ListDocumentChunksCommandOutput;
    };
  };
}
