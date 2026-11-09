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
import type { GetSourceUploadUrlsInput, GetSourceUploadUrlsOutput } from "../models/models_0";
import { GetSourceUploadUrls$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetSourceUploadUrlsCommand}.
 */
export interface GetSourceUploadUrlsCommandInput extends GetSourceUploadUrlsInput {}
/**
 * @public
 *
 * The output of {@link GetSourceUploadUrlsCommand}.
 */
export interface GetSourceUploadUrlsCommandOutput extends GetSourceUploadUrlsOutput, __MetadataBearer {}

/**
 * Generate pre-signed S3 upload URLs for DOCUMENTS sources (upload flow).
 *
 * Takes no clientToken: it writes no record. Each call mints a fresh uploadId
 * and URLs; an abandoned set simply expires, so a retry is harmless.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetSourceUploadUrlsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetSourceUploadUrlsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetSourceUploadUrlsInput
 *   namespaceId: "STRING_VALUE", // required
 *   files: [ // UploadFileRequestList // required
 *     { // UploadFileRequest
 *       filename: "STRING_VALUE", // required
 *       contentType: "STRING_VALUE", // required
 *     },
 *   ],
 * };
 * const command = new GetSourceUploadUrlsCommand(input);
 * const response = await client.send(command);
 * // { // GetSourceUploadUrlsOutput
 * //   uploadId: "STRING_VALUE", // required
 * //   s3Prefix: "STRING_VALUE", // required
 * //   uploadUrls: [ // UploadUrlList // required
 * //     { // UploadUrl
 * //       filename: "STRING_VALUE", // required
 * //       uploadUrl: "STRING_VALUE", // required
 * //     },
 * //   ],
 * //   expiresIn: Number("int"), // required
 * // };
 *
 * ```
 *
 * @param GetSourceUploadUrlsCommandInput - {@link GetSourceUploadUrlsCommandInput}
 * @returns {@link GetSourceUploadUrlsCommandOutput}
 * @see {@link GetSourceUploadUrlsCommandInput} for command's `input` shape.
 * @see {@link GetSourceUploadUrlsCommandOutput} for command's `response` shape.
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
 * @example Request an upload URL for a PDF document
 * ```javascript
 * //
 * const input = {
 *   files: [
 *     {
 *       contentType: "application/pdf",
 *       filename: "q3-revenue-report.pdf"
 *     }
 *   ],
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
 * };
 * const command = new GetSourceUploadUrlsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   expiresIn: 3600,
 *   s3Prefix: "uploads/b7e2c4a0-1f3d-4e6b-8a2c-9d0e1f2a3b4c/",
 *   uploadId: "b7e2c4a0-1f3d-4e6b-8a2c-9d0e1f2a3b4c",
 *   uploadUrls: [
 *     {
 *       filename: "q3-revenue-report.pdf",
 *       uploadUrl: "https://example-bucket.s3.amazonaws.com/uploads/b7e2c4a0/q3-revenue-report.pdf?X-Amz-Signature=abc123"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetSourceUploadUrlsCommand extends $Command
  .classBuilder<
    GetSourceUploadUrlsCommandInput,
    GetSourceUploadUrlsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetSourceUploadUrls", {})
  .n("ControlPlaneServiceClient", "GetSourceUploadUrlsCommand")
  .sc(GetSourceUploadUrls$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetSourceUploadUrlsInput;
      output: GetSourceUploadUrlsOutput;
    };
    sdk: {
      input: GetSourceUploadUrlsCommandInput;
      output: GetSourceUploadUrlsCommandOutput;
    };
  };
}
