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
import type { GetOsiUploadUrlInput, GetOsiUploadUrlOutput } from "../models/models_0";
import { GetOsiUploadUrl$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetOsiUploadUrlCommand}.
 */
export interface GetOsiUploadUrlCommandInput extends GetOsiUploadUrlInput {}
/**
 * @public
 *
 * The output of {@link GetOsiUploadUrlCommand}.
 */
export interface GetOsiUploadUrlCommandOutput extends GetOsiUploadUrlOutput, __MetadataBearer {}

/**
 * Generate a pre-signed S3 PUT URL for uploading large OSI YAML files.
 * After uploading, call ImportOsi with the returned s3Key.
 *
 * Takes no `clientToken`: it creates no server-side resource. A retry mints a
 * fresh URL under a new key; an unused URL simply expires.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetOsiUploadUrlCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetOsiUploadUrlCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetOsiUploadUrlInput
 *   namespaceId: "STRING_VALUE", // required
 *   filename: "STRING_VALUE", // required
 * };
 * const command = new GetOsiUploadUrlCommand(input);
 * const response = await client.send(command);
 * // { // GetOsiUploadUrlOutput
 * //   uploadUrl: "STRING_VALUE", // required
 * //   s3Key: "STRING_VALUE", // required
 * //   expiresIn: Number("int"), // required
 * // };
 *
 * ```
 *
 * @param GetOsiUploadUrlCommandInput - {@link GetOsiUploadUrlCommandInput}
 * @returns {@link GetOsiUploadUrlCommandOutput}
 * @see {@link GetOsiUploadUrlCommandInput} for command's `input` shape.
 * @see {@link GetOsiUploadUrlCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
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
 * @example Request a pre-signed upload URL
 * ```javascript
 * //
 * const input = {
 *   filename: "metrics-export.yaml",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new GetOsiUploadUrlCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   expiresIn: 900,
 *   s3Key: "sales-analytics/01HZY8K3M4N5P6Q7R8S9T0V1W2.yaml",
 *   uploadUrl: "https://coa-osi-uploads.s3.amazonaws.com/sales-analytics/01HZY8K3M4N5P6Q7R8S9T0V1W2.yaml?X-Amz-Signature=abc123"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetOsiUploadUrlCommand extends $Command
  .classBuilder<
    GetOsiUploadUrlCommandInput,
    GetOsiUploadUrlCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetOsiUploadUrl", {})
  .n("ControlPlaneServiceClient", "GetOsiUploadUrlCommand")
  .sc(GetOsiUploadUrl$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetOsiUploadUrlInput;
      output: GetOsiUploadUrlOutput;
    };
    sdk: {
      input: GetOsiUploadUrlCommandInput;
      output: GetOsiUploadUrlCommandOutput;
    };
  };
}
