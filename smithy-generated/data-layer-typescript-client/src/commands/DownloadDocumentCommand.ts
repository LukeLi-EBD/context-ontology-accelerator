// smithy-typescript generated code
import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { Command as $Command } from "@smithy/smithy-client";
import type { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { Uint8ArrayBlobAdapter } from "@smithy/util-stream";

import type {
  DataLayerServiceClientResolvedConfig,
  ServiceInputTypes,
  ServiceOutputTypes,
} from "../DataLayerServiceClient";
import { commonParams } from "../endpoint/EndpointParameters";
import type { DownloadDocumentInput, DownloadDocumentOutput } from "../models/models_0";
import { DownloadDocument$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DownloadDocumentCommand}.
 */
export interface DownloadDocumentCommandInput extends DownloadDocumentInput {}
/**
 * @public
 */
export type DownloadDocumentCommandOutputType = Omit<DownloadDocumentOutput, "content"> & {
  content?: Uint8ArrayBlobAdapter;
};

/**
 * @public
 *
 * The output of {@link DownloadDocumentCommand}.
 */
export interface DownloadDocumentCommandOutput extends DownloadDocumentCommandOutputType, __MetadataBearer {}

/**
 * Download the stored bytes of one document.
 *
 * The body is the exact byte sequence stored at upload — no normalisation and
 * no re-serialisation — so a client can verify it against
 * `UploadDocument.contentHash` with a plain digest comparison.
 *
 * `X-Content-Sha256` repeats that digest for the returned bytes. A document
 * stored with zero bytes answers 200 with an empty body and the SHA-256 of the
 * empty string; only an unknown document answers `NotFoundError`.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { DataLayerServiceClient, DownloadDocumentCommand } from "@coa/data-layer-client"; // ES Modules import
 * // const { DataLayerServiceClient, DownloadDocumentCommand } = require("@coa/data-layer-client"); // CommonJS import
 * // import type { DataLayerServiceClientConfig } from "@coa/data-layer-client";
 * const config = {}; // type is DataLayerServiceClientConfig
 * const client = new DataLayerServiceClient(config);
 * const input = { // DownloadDocumentInput
 *   namespaceId: "STRING_VALUE", // required
 *   documentId: "STRING_VALUE", // required
 * };
 * const command = new DownloadDocumentCommand(input);
 * const response = await client.send(command);
 * // { // DownloadDocumentOutput
 * //   content: new Uint8Array(),
 * //   contentSha256: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param DownloadDocumentCommandInput - {@link DownloadDocumentCommandInput}
 * @returns {@link DownloadDocumentCommandOutput}
 * @see {@link DownloadDocumentCommandInput} for command's `input` shape.
 * @see {@link DownloadDocumentCommandOutput} for command's `response` shape.
 * @see {@link DataLayerServiceClientResolvedConfig | config} for DataLayerServiceClient's `config` shape.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
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
 * @example Download the bytes of a stored document
 * ```javascript
 * //
 * const input = {
 *   documentId: "9a7b6c5d-4e3f-4a2b-8c1d-0e9f8a7b6c5d",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new DownloadDocumentCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   content: "SGVsbG8sIHdvcmxkIQ==",
 *   contentSha256: "d9014c4624844aa5bac314773d6b689ad467fa4e1d1a50a1b8b2e1e5c1c0e5b8"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class DownloadDocumentCommand extends $Command
  .classBuilder<
    DownloadDocumentCommandInput,
    DownloadDocumentCommandOutput,
    DataLayerServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: DataLayerServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("DataLayerService", "DownloadDocument", {})
  .n("DataLayerServiceClient", "DownloadDocumentCommand")
  .sc(DownloadDocument$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: DownloadDocumentInput;
      output: DownloadDocumentOutput;
    };
    sdk: {
      input: DownloadDocumentCommandInput;
      output: DownloadDocumentCommandOutput;
    };
  };
}
