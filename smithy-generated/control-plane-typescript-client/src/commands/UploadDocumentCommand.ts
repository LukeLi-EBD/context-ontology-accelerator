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
import type { UploadDocumentInput, UploadDocumentOutput } from "../models/models_0";
import { UploadDocument$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UploadDocumentCommand}.
 */
export interface UploadDocumentCommandInput extends UploadDocumentInput {}
/**
 * @public
 *
 * The output of {@link UploadDocumentCommand}.
 */
export interface UploadDocumentCommandOutput extends UploadDocumentOutput, __MetadataBearer {}

/**
 * Store a document's bytes and register it for ingestion.
 *
 * `contentBase64` carries the bytes. The content hash is computed server-side
 * from the decoded bytes, so the returned `contentHash` is always the hash of
 * what was stored; `contentSha256`, when supplied, is verified against it.
 * Re-uploading identical bytes into the same namespace answers 409 with the
 * existing document id.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, UploadDocumentCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, UploadDocumentCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // UploadDocumentInput
 *   namespaceId: "STRING_VALUE", // required
 *   filename: "STRING_VALUE", // required
 *   contentType: "STRING_VALUE", // required
 *   contentBase64: "STRING_VALUE",
 *   contentSha256: "STRING_VALUE",
 *   title: "STRING_VALUE",
 *   metadata: { // DocumentMetadata
 *     "<keys>": "STRING_VALUE",
 *   },
 * };
 * const command = new UploadDocumentCommand(input);
 * const response = await client.send(command);
 * // { // UploadDocumentOutput
 * //   documentId: "STRING_VALUE", // required
 * //   version: Number("int"), // required
 * //   contentHash: "STRING_VALUE", // required
 * //   status: "UPLOADED" || "PROCESSING" || "INDEXED" || "FAILED", // required
 * // };
 *
 * ```
 *
 * @param UploadDocumentCommandInput - {@link UploadDocumentCommandInput}
 * @returns {@link UploadDocumentCommandOutput}
 * @see {@link UploadDocumentCommandInput} for command's `input` shape.
 * @see {@link UploadDocumentCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Upload a plain-text policy
 * ```javascript
 * //
 * const input = {
 *   contentBase64: "5L+d6K+B6LS35qy+5pS/562W",
 *   contentType: "text/plain",
 *   filename: "loan-policy.txt",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new UploadDocumentCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   contentHash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
 *   documentId: "9a7b6c5d-4e3f-4a2b-8c1d-0e9f8a7b6c5d",
 *   status: "PROCESSING",
 *   version: 1
 * }
 * *\/
 * ```
 *
 * @public
 */
export class UploadDocumentCommand extends $Command
  .classBuilder<
    UploadDocumentCommandInput,
    UploadDocumentCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "UploadDocument", {})
  .n("ControlPlaneServiceClient", "UploadDocumentCommand")
  .sc(UploadDocument$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: UploadDocumentInput;
      output: UploadDocumentOutput;
    };
    sdk: {
      input: UploadDocumentCommandInput;
      output: UploadDocumentCommandOutput;
    };
  };
}
